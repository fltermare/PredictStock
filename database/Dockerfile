FROM postgres

COPY *.sql /docker-entrypoint-initdb.d/
# COPY *.bash /docker-entrypoint-initdb.d/
COPY *.bash /
ADD sampledata /data
