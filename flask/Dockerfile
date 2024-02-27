FROM python:3.9-alpine

WORKDIR usr/src/flask_app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ./app .