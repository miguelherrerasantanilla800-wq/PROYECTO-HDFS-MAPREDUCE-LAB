# Atajos. Requiere Docker + Docker Compose v2 + bash (en Windows: Git Bash o WSL2).
SH = bash

.PHONY: help up load jobs verify airflow-up airflow-trigger airflow-down ft-datanode ft-nodemanager ft-put test-local all status down clean

help:           ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

up:             ## Construye imagen y levanta el clúster (8 contenedores)
	$(SH) scripts/00_up.sh
load:           ## Prepara el JSON de transacciones y lo sube a HDFS
	$(SH) scripts/01_load_data.sh
jobs:           ## Ejecuta cinco análisis MapReduce de transacciones
	$(SH) scripts/02_run_jobs.sh
verify:         ## Verifica HDFS/YARN/jobs/logs y valida resultados
	$(SH) scripts/03_verify.sh
airflow-up: up  ## Levanta Airflow y el clúster para orquestar el pipeline
	docker compose --profile airflow up -d --build airflow-webserver airflow-scheduler
airflow-trigger: ## Dispara el pipeline de transacciones en Airflow
	docker compose --profile airflow exec airflow-webserver airflow dags unpause transactions_pipeline
	docker compose --profile airflow exec airflow-webserver airflow dags trigger transactions_pipeline
airflow-down:   ## Detiene Airflow (conserva su base de metadatos)
	docker compose --profile airflow stop airflow-webserver airflow-scheduler airflow-postgres
ft-datanode:    ## Experimento A: falla de un DataNode
	$(SH) scripts/04_ft_datanode.sh
ft-nodemanager: ## Experimento B: falla de un NodeManager con job en ejecución
	$(SH) scripts/05_ft_nodemanager.sh
ft-put:         ## Experimento C: reiniciar DataNode durante una escritura
	$(SH) scripts/06_ft_restart_put.sh
test-local:     ## Prueba de mappers/reducers SIN Hadoop (requiere python3 en el host)
	$(SH) tests/local_test.sh
all: up load jobs verify ## Todo lo básico, de principio a fin

status:         ## Estado rápido del clúster
	@docker exec namenode hdfs dfsadmin -report | grep -E "Live|Dead|Under"; docker exec namenode yarn node -list -all
down:           ## Detiene Hadoop y Airflow (conserva volúmenes y datos)
	docker compose down
clean:          ## Destruye TODO: contenedores, volúmenes (HDFS), datos y resultados
	docker compose down -v
	rm -rf data results results_local data_local_test
