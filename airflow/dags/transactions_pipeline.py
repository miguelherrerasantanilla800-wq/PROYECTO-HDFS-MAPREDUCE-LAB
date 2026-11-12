"""Pipeline orquestado: prepara JSONL, carga HDFS, ejecuta MapReduce y valida."""
import logging
from datetime import datetime, timedelta

import docker
from airflow import DAG
from airflow.operators.python import PythonOperator

LOGGER = logging.getLogger(__name__)
TRANSACTION_JOBS = (
    "avg_by_category",
    "peak_hours",
    "top_merchants",
    "fraud_by_city",
    "payment_methods",
)


def run_in_namenode(command, task_name):
    client = docker.from_env(timeout=1800)
    try:
        namenode = client.containers.get("namenode")
        result = namenode.exec_run(["bash", "-lc", command], demux=True)
    finally:
        client.close()

    stdout, stderr = result.output
    output = b"\n".join(part for part in (stdout, stderr) if part).decode(
        "utf-8", errors="replace"
    )
    if output:
        LOGGER.info("%s output:\n%s", task_name, output[-12000:])
    if result.exit_code != 0:
        raise RuntimeError(
            f"{task_name} terminó con código {result.exit_code}.\n{output[-4000:]}"
        )


def prepare_transactions():
    run_in_namenode(
        "python3 /lab/scripts/prepare_transactions.py "
        "--input /lab/source/dataset_transacciones_1_millon.json "
        "--output /lab/data/transactions",
        "prepare_transactions",
    )


def load_transactions():
    run_in_namenode(
        "hdfs dfs -rm -r -f -skipTrash /lab/input/transactions && "
        "hdfs dfs -mkdir -p /lab/input/transactions && "
        "hdfs dfs -D dfs.blocksize=16777216 -put -f "
        "/lab/data/transactions/part-*.jsonl /lab/input/transactions/",
        "load_transactions",
    )


def run_transaction_job(job_name):
    if job_name not in TRANSACTION_JOBS:
        raise ValueError(f"Análisis de transacciones desconocido: {job_name}")
    run_in_namenode(
        f"HADOOP_CONTAINER_LOCAL=1 bash /lab/scripts/run_transaction_job.sh {job_name}",
        job_name,
    )


def validate_results():
    run_in_namenode(
        "python3 /lab/scripts/validate.py --data /lab/data --results /lab/results",
        "validate_results",
    )


default_args = {
    "owner": "data-engineering-lab",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="transactions_pipeline",
    description="Prepara, carga, analiza y valida el dataset de transacciones en Hadoop.",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["hadoop", "mapreduce", "transacciones"],
) as dag:
    prepare = PythonOperator(
        task_id="prepare_jsonl",
        python_callable=prepare_transactions,
    )
    load = PythonOperator(
        task_id="load_hdfs",
        python_callable=load_transactions,
    )
    jobs = [
        PythonOperator(
            task_id=f"run_{job_name}",
            python_callable=run_transaction_job,
            op_kwargs={"job_name": job_name},
        )
        for job_name in TRANSACTION_JOBS
    ]
    validate = PythonOperator(
        task_id="validate_outputs",
        python_callable=validate_results,
    )

    previous = prepare >> load
    for job in jobs:
        previous = previous >> job
    previous >> validate
