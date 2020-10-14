FROM python:3.8-slim-buster

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY *.py /app/
ADD ./core /app/core
# ADD ./static /app/static
# ADD ./templates /app/templates
