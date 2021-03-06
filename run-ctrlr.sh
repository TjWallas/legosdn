#!/usr/bin/env bash
# -*- mode: sh; coding: utf-8; fill-column: 80; -*-
#
# run-ctrlr.sh
# Created by Balakrishnan Chandrasekaran on 2015-09-20 15:41 -0400.
#

if [ ${JAVA_HOME:-''} == '' ]; then
    echo 'Error: JAVA_HOME not set!' 1>&2
    exit 1
fi

if [ ${FLOODLIGHT_HOME:-''} == '' ]; then
    echo 'Error: FLOODLIGHT_HOME not set!' 1>&2
    exit 1
fi

if [ ${LEGOSDN_RT:-''} == '' ]; then
    echo 'Error: LEGOSDN_RT not set!' 1>&2
    exit 1
fi

JAVA="${JAVA_HOME}/bin/java"

FL_JAR="${FLOODLIGHT_HOME}/target/floodlight.jar"
FL_LOGBACK="${LEGOSDN_RT}/conf/logback.xml"
if [ ! -f ${FL_LOGBACK} ]; then
    echo "Error: Cannot find '${FL_LOGBACK}'" 1>&2
    exit 1
fi

JVM_OPTS=""
JVM_OPTS="${JVM_OPTS} -server -d64"
JVM_OPTS="${JVM_OPTS} -Xmx512m -Xms512m -Xmn160m"
# Turn off jvmstat instrumentation
JVM_OPTS="${JVM_OPTS} -XX:-UsePerfData"
JVM_OPTS="${JVM_OPTS} -XX:+UseParallelGC -XX:+AggressiveOpts -XX:+UseFastAccessorMethods"
JVM_OPTS="${JVM_OPTS} -XX:MaxInlineSize=8192 -XX:FreqInlineSize=8192"
JVM_OPTS="${JVM_OPTS} -XX:CompileThreshold=1500"
JVM_OPTS="${JVM_OPTS} -Dpython.security.respectJavaAccessibility=false"

# Create a logback file if required
[ -f ${FL_LOGBACK} ] || cat <<EOF_LOGBACK >${FL_LOGBACK}
<configuration scan="true">
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%level [%logger:%thread] %msg%n</pattern>
        </encoder>
    </appender>
    <root level="INFO">
        <appender-ref ref="STDOUT" />
    </root>
    <logger name="org" level="WARN"/>
    <logger name="LogService" level="WARN"/> <!-- Restlet access logging -->
    <logger name="net.floodlightcontroller" level="INFO"/>
    <logger name="net.floodlightcontroller.logging" level="ERROR"/>
</configuration>
EOF_LOGBACK

echo "Starting floodlight server ..."

${JAVA} ${JVM_OPTS} \
    -Dlogback.configurationFile=${FL_LOGBACK} \
    -jar ${FL_JAR}
