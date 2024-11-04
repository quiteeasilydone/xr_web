FROM python:3.9

RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libavdevice-dev \
    libavfilter-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    && apt-get clean
WORKDIR /usr/src/fastapi_app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install reportlab
COPY ./app .