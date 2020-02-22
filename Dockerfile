FROM ubuntu:18.04

LABEL Author="Albert Su"
LABEL E-mail="fltermare@gmail.com"
LABEL version="0.0.1"

RUN apt-get update && apt-get upgrade -y

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8

RUN apt-get install -y python3.6 python3-pip python3.6-dev

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/

RUN python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install -r requirements.txt

ADD . /app
RUN rm -rf /app/airflow/Envs /app/airflow/logs
RUN echo n | python3 run.py --init

EXPOSE 5000 8080
CMD ["python3", "run.py", "--start", "--update"]
