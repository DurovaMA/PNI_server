FROM python:3.9-slim as build
WORKDIR /app

COPY requirements.txt /app/

RUN apt-get update
RUN apt-get -y install g++ libpq-dev gcc unixodbc unixodbc-dev

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"


RUN pip install -r requirements.txt

FROM python:3.9-slim as prod

RUN apt-get update
RUN apt install -y libpq5
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY ./app/ /app/

WORKDIR /

EXPOSE 5005

RUN chmod a+rwx /app/api/config.txt

ENTRYPOINT  ["python3", "-m","app.api.server","--config","/app/api/config.txt"]
