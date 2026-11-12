# Pipeline de transacciones: Airflow + Hadoop + HDFS

Proyecto local de procesamiento distribuido con Docker Compose, Apache Airflow y Hadoop 3.3.6. Airflow coordina
el flujo; Hadoop Streaming ejecuta cinco análisis MapReduce sobre el dataset de un millón de transacciones.

## Arquitectura

```mermaid
flowchart LR
    JSON["dataset_transacciones_1_millon.json<br/>archivo original, solo lectura"]
    PREP["Airflow task<br/>prepare_jsonl"]
    PARTS["data/transactions/<br/>10 partes JSONL"]
    LOAD["Airflow task<br/>load_hdfs"]
    HDFS["HDFS<br/>/lab/input/transactions"]
    subgraph AIRFLOW["Airflow: UI + Scheduler + LocalExecutor"]
        direction TB
        DAG["transactions_pipeline DAG"]
        PREP --> LOAD
        LOAD --> J1["run_avg_by_category"]
        J1 --> J2["run_peak_hours"]
        J2 --> J3["run_top_merchants"]
        J3 --> J4["run_fraud_by_city"]
        J4 --> J5["run_payment_methods"]
        J5 --> VALID["validate_outputs"]
    end
    JSON --> PREP
    PREP --> PARTS
    PARTS --> LOAD
    LOAD --> HDFS
    HDFS --> JOBS["YARN + Hadoop Streaming<br/>NameNode / NodeManagers"]
    JOBS --> RESULTS["HDFS /lab/output/<job><br/>y también results/*.tsv"]
    RESULTS --> VALID
    META["PostgreSQL<br/>estado de Airflow y ejecuciones"] --- AIRFLOW
```

### Componentes

| Componente                             | Responsabilidad                                                                          |
| -------------------------------------- | ---------------------------------------------------------------------------------------- |
| Airflow webserver (`localhost:8080`) | Interfaz para ver el DAG, lanzarlo y consultar logs/estado de cada tarea                 |
| Airflow scheduler                      | Programa y administra tareas; usa `LocalExecutor` para este laboratorio                |
| PostgreSQL                             | Guarda metadatos de Airflow: DAG runs, estados, usuarios y tareas; no guarda el dataset  |
| NameNode                               | Prepara el JSONL, recibe comandos del DAG, accede al dataset y ejecuta el cliente Hadoop |
| HDFS / DataNodes                       | Guarda las partes de entrada y los resultados distribuidos                               |
| YARN / NodeManagers                    | Ejecuta los mappers y reducers de cada análisis                                         |

Airflow se comunica con el NameNode mediante la API local de Docker (`/var/run/docker.sock`) para ejecutar los
comandos del flujo. Esta configuración es práctica para un laboratorio en una sola máquina, pero el socket concede
control amplio sobre Docker: úsala solo en un entorno local confiable, no la expongas a Internet ni la copies tal
cual a producción.

## Datos y persistencia

El archivo original debe estar en la carpeta padre de `hdfs-mapreduce-lab/`, como en este workspace. Docker lo monta
en el NameNode como `/lab/source/dataset_transacciones_1_millon.json` **en solo lectura**. El DAG no modifica ni
reemplaza el original.

La tarea `prepare_jsonl` convierte por streaming el arreglo JSON (una sola línea) en archivos JSONL con 100.000
registros por archivo. Así Hadoop puede dividir la entrada en splits y ejecutar múltiples mappers. Las partes se
guardan localmente en `data/transactions/` y se cargan a HDFS en `/lab/input/transactions/`. HDFS almacena sus
bloques en los volúmenes de Docker de los DataNodes.

Cada job guarda su salida en HDFS bajo `/lab/output/<nombre-del-job>/`; además, se copia un TSV a `results/` para
consultarlo desde el host. La base de datos de Airflow y los logs de tareas tienen volúmenes propios.

`make down` detiene y elimina los contenedores, pero conserva los volúmenes y datos. `make clean` elimina también
los volúmenes de HDFS/PostgreSQL/Airflow, las partes generadas y los resultados locales.

## Inicio rápido

Requisitos: Docker + Docker Compose v2, y al menos 8 GB de RAM disponibles para Docker. En Windows usa Git Bash o
WSL2 con integración de Docker Desktop habilitada. La primera construcción descarga Hadoop y la imagen de Airflow.

Desde `hdfs-mapreduce-lab/`:

```bash
cp .env.example .env       # configura credenciales locales de Airflow
make airflow-up            # inicia Hadoop y Airflow; la primera vez puede tardar
make airflow-trigger       # lanza el DAG de transacciones
```

Abre [http://localhost:8080](http://localhost:8080), inicia sesión con las credenciales de `.env` y selecciona `transactions_pipeline`.
El DAG se crea pausado; actívalo y pulsa **Trigger DAG**. El comando `make airflow-trigger` lo activa si hace falta
y dispara una ejecución desde la terminal. El DAG está configurado sin calendario (`schedule=None`) porque el dataset
actual es estático: se ejecuta cuando lo disparas y no procesa el mismo millón de registros cada día por accidente.
Si el clúster ya se inició sin crear `.env`, las credenciales locales iniciales son `admin` / `admin`; en un primer
arranque nuevo, copia `.env.example` antes de iniciar los servicios y define una contraseña propia.

El DAG contiene tareas encadenadas para que los jobs no compitan entre sí por los recursos limitados del clúster.
Airflow reintenta una vez las tareas que fallan, y `validate_outputs` compara las cinco salidas con un recálculo
independiente. El run solo termina exitosamente si la validación pasa.

### Ejecución manual sin Airflow

El flujo Hadoop anterior sigue disponible:

```bash
make up
make load
make jobs
make verify
make test-local
```

## Análisis MapReduce

| Job                 | Agrupación     | Salida                                                  |
| ------------------- | --------------- | ------------------------------------------------------- |
| `avg_by_category` | Categoría      | Monto promedio, monto total y cantidad de transacciones |
| `peak_hours`      | Hora del día   | Número de transacciones por hora                       |
| `top_merchants`   | Comercio        | Los 10 comercios con más transacciones                 |
| `fraud_by_city`   | Ciudad          | Cantidad fraudulenta, total y tasa de fraude            |
| `payment_methods` | Método de pago | Cantidad de transacciones y monto total                 |

Los combiners agregan sumas y conteos (no promedios parciales). Los registros inválidos se omiten y se registran en
contadores de Hadoop.

## Configuración

Las variables opcionales están en `.env.example`; copia el archivo a `.env` y cambia la contraseña antes de iniciar
Airflow:

| Variable                   | Uso                                                                                                              |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `AIRFLOW_ADMIN_USERNAME` | Usuario administrador de la UI (por defecto `admin`)                                                           |
| `AIRFLOW_ADMIN_PASSWORD` | Contraseña local de la UI (el ejemplo es solo para desarrollo)                                                  |
| `AIRFLOW_UID`            | UID con el que corre Airflow en Linux                                                                            |
| `DOCKER_GID`             | Grupo dueño del socket Docker en Linux/WSL; si hay error de permisos, usa `stat -c '%g' /var/run/docker.sock` |

El usuario se crea durante la inicialización de Airflow y no se duplica si ya existe. Si cambias la contraseña en
`.env` después de que ese usuario fue creado, actualízala en Airflow o elimina la base de datos **solo si aceptas
perder el historial y usuarios** (`make clean` borra todos los volúmenes).

## Comandos útiles

```bash
make airflow-up        # iniciar Hadoop y Airflow
make airflow-trigger   # disparar transactions_pipeline
make airflow-down      # detener Airflow sin borrar su base de datos
make verify            # validar las salidas existentes
make down              # detener todos los contenedores, conservar volúmenes
make clean             # eliminar contenedores, volúmenes y datos generados
```

Interfaces del clúster: HDFS [http://localhost:9870](http://localhost:9870), YARN [http://localhost:8088](http://localhost:8088) e historial MapReduce
[http://localhost:19888](http://localhost:19888).

Para consultar una salida en HDFS: `docker exec namenode hdfs dfs -cat /lab/output/top_merchants/part-*`.
Las copias de resultados locales están en `results/*.tsv`.

## Preguntas frecuentes

**¿Airflow procesa o guarda el JSON?**
No. Airflow coordina tareas. El NameNode lee el JSON original montado en solo lectura, lo convierte a JSONL y
Hadoop procesa las partes en HDFS.

**¿Dónde se guardan los datos?**
El original permanece en su ubicación; las partes convertidas quedan en `data/transactions/`; la entrada procesable
y las salidas de jobs quedan en HDFS, respaldado por volúmenes Docker; las salidas TSV también quedan en `results/`.
PostgreSQL solo guarda metadatos de Airflow.

**¿Qué pasa si falla un job?**
Airflow muestra el log de esa tarea y la reintenta una vez. Si sigue fallando, las tareas posteriores quedan
bloqueadas y el DAG aparece como fallido; corrige la causa y vuelve a dispararlo.

**¿Se ejecuta automáticamente cada día?**
No. El dataset es estático y el DAG es manual para evitar reprocesar la misma entrada sin necesidad. Si luego se
incorporan archivos nuevos periódicamente, se puede definir un calendario o un sensor de archivos.

**¿Puedo correr solo Hadoop?**
Sí. Usa `make up`, `make load`, `make jobs` y `make verify`; Airflow es opcional.

**¿Cómo borro Airflow sin borrar el historial?**
`make airflow-down` detiene sus servicios y conserva PostgreSQL. `make down` detiene todo y conserva los volúmenes.
`make clean` sí elimina los volúmenes, el historial y los resultados generados.

## Tolerancia a fallos (experimentos del laboratorio)

```bash
make ft-datanode
make ft-nodemanager
make ft-put
```

Estos experimentos interrumpen nodos Hadoop para observar re-replicación HDFS y reintentos de tareas. Airflow no
reemplaza los mecanismos de recuperación de HDFS/YARN.
