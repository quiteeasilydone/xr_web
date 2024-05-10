FROM ubuntu:latest

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    libmicrohttpd-dev libjansson-dev \
    libssl-dev libsofia-sip-ua-dev libglib2.0-dev \
    libopus-dev libogg-dev libcurl4-openssl-dev liblua5.3-dev \
    libconfig-dev pkg-config libtool automake \
    git wget cmake meson ninja-build \
    sed aptitude doxygen graphviz

# libnice 설치
RUN git clone https://gitlab.freedesktop.org/libnice/libnice && \
    cd libnice && \
    meson --prefix=/usr build && \
    ninja -C build && \
    ninja -C build install

# libsrtp 설치
RUN wget https://github.com/cisco/libsrtp/archive/v2.2.0.tar.gz && \
    tar xfv v2.2.0.tar.gz && \
    cd libsrtp-2.2.0 && \
    ./configure --prefix=/usr --enable-openssl && \
    make shared_library && \
    make install

# BoringSSL 설치
RUN git clone https://boringssl.googlesource.com/boringssl && \
    cd boringssl && \
    sed -i s/" -Werror"//g CMakeLists.txt && \
    mkdir -p build && \
    cd build && \
    cmake -DCMAKE_CXX_FLAGS="-lrt" .. && \
    make && \
    mkdir -p /opt/boringssl && \
    cp -R ../include /opt/boringssl/ && \
    mkdir -p /opt/boringssl/lib && \
    cp ssl/libssl.a /opt/boringssl/lib/ && \
    cp crypto/libcrypto.a /opt/boringssl/lib/

# usrsctp 설치
RUN git clone https://github.com/sctplab/usrsctp && \
    cd usrsctp && \
    ./bootstrap && \
    ./configure --prefix=/usr --disable-programs --disable-inet --disable-inet6 && \
    make && \
    make install

# libwebsockets 설치
RUN git clone https://github.com/warmcat/libwebsockets.git && \
    cd libwebsockets && \
    mkdir build && \
    cd build && \
    cmake -DLWS_MAX_SMP=1 -DLWS_WITHOUT_EXTENSIONS=0 -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_C_FLAGS="-fpic" .. && \
    make && \
    make install

# Paho MQTT C client library 설치
RUN git clone https://github.com/eclipse/paho.mqtt.c.git && \
    cd paho.mqtt.c && \
    make && \
    make install

# Nanomsg library 설치
RUN aptitude install -y libnanomsg-dev

# RabbitMQ C client library 설치
RUN git clone https://github.com/alanxz/rabbitmq-c && \
    cd rabbitmq-c && \
    git submodule init && \
    git submodule update && \
    mkdir build && \
    cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr .. && \
    make && \
    make install

# 모든 패키지 설치 완료 후 필요없는 파일 정리
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Janus WebRTC Gateway가 실행될 때 필요한 환경 설정 등 구성
# 여기에 Janus 서버를 구동하기 위한 추가적인 스크립트나 명령어를 추가하세요.
RUN export JANUS_WITH_POSTPROCESSING
RUN  set -x \
    && git clone https://github.com/meetecho/janus-gateway.git \
    && cd janus-gateway \
    && sh autogen.sh \
    && ./configure --prefix=/opt/janus \
    && make \
    && make install \
    && make configs

COPY ./conf /opt/janus/etc/janus

RUN adduser --disabled-password --gecos '' janus
USER root
# RUN /opt/janus/bin/janus --v
CMD ["/opt/janus/bin/janus"]