# Imagen única para todos los roles (NameNode, DataNode, ResourceManager, NodeManager, HistoryServer).
# Incluye Python 3 para poder ejecutar jobs con Hadoop Streaming.
FROM eclipse-temurin:11-jdk-jammy

ARG HADOOP_VERSION=3.3.6
ARG HADOOP_URL=https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz

ENV HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    LANG=C.UTF-8 \
    PYTHONIOENCODING=utf-8
ENV PATH=${PATH}:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 curl procps iputils-ping net-tools less ca-certificates \
 && ln -s /usr/bin/python3 /usr/bin/python \
 && rm -rf /var/lib/apt/lists/*

# Descarga de Hadoop (~700 MB, solo ocurre en el primer build)
RUN curl -fSL "${HADOOP_URL}" -o /tmp/hadoop.tgz \
 && tar -xzf /tmp/hadoop.tgz -C /opt \
 && mv /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} \
 && rm -rf /tmp/hadoop.tgz ${HADOOP_HOME}/share/doc \
 && echo "export JAVA_HOME=${JAVA_HOME}" >> ${HADOOP_CONF_DIR}/hadoop-env.sh

RUN useradd -m -s /bin/bash hadoop \
 && mkdir -p /hadoop-data/name /hadoop-data/data /hadoop-data/tmp /lab/data /lab/results /lab/jobs /lab/scripts

COPY conf/*.xml ${HADOOP_CONF_DIR}/
COPY entrypoint.sh /entrypoint.sh
# sed: tolera checkouts con finales de línea CRLF (Windows)
RUN sed -i 's/\r$//' /entrypoint.sh \
 && chmod +x /entrypoint.sh \
 && chown -R hadoop:hadoop /opt/hadoop /hadoop-data /lab

USER hadoop
WORKDIR /home/hadoop
ENTRYPOINT ["/entrypoint.sh"]
