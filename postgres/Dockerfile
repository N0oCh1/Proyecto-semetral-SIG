# PostgreSQL del proyecto: zona horaria de Panamá para que las fechas no se corran al guardar
FROM postgres:17

ENV TZ=America/Panama \
    PGTZ=America/Panama

# Los .sql de postgres/init/ corren solo la primera vez, cuando el volumen de datos está vacío
COPY init/ /docker-entrypoint-initdb.d/
