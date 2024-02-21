FROM python:3.9-slim
WORKDIR /app

COPY requirements.txt /app/

RUN apt-get update
RUN apt-get -y install g++ libpq-dev gcc unixodbc unixodbc-dev
RUN pip install psycopg2

RUN pip install -r requirements.txt

COPY ./app/ /app/

WORKDIR /

EXPOSE 5005

RUN chmod a+rwx /app/api/config.txt

ENTRYPOINT  ["python3", "-m","app.api.server","--config","/app/api/config.txt"]
