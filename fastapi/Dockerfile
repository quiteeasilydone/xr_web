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
    fonts-noto-cjk \
    && apt-get clean
WORKDIR /usr/src/fastapi_app

COPY ./fonts /usr/share/fonts/opentype/noto
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install reportlab
RUN pip install requests
RUN fc-cache -fv
COPY ./app .