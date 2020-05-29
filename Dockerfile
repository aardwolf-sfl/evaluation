FROM ubuntu:18.04

# === SYSTEM ===

RUN apt-get update && apt-get install -y \
    llvm-9 \
    clang-9 \
    cmake \
    python3.8 \
    python3-pip \
    time \
    autoconf \
    libtool \
    gcc \
    g++ \
    python3.8-dev

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-9 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1
# python3.8-pip does not exist in 18.04 repositories and default python3-pip uses python 3.6
RUN echo '#!/bin/sh' > /usr/bin/pip
RUN echo 'python -m pip $@' >> /usr/bin/pip
RUN chmod +x /usr/bin/pip

RUN apt-get install -y libjpeg-dev python3-distutils python3-setuptools
RUN pip install pytest

# === RESOURCES ===

WORKDIR /root

COPY libtiff libtiff
COPY matplotlib matplotlib

WORKDIR /root/libtiff
RUN bash autogen.sh
RUN cp test-driver.patch config/test-driver
WORKDIR /root/matplotlib
RUN mv setup.cfg.template setup.cfg
RUN echo "[test]\nlocal_freetype = True\ntests = True" >> setup.cfg
RUN python -mpip install -ve .
RUN python setup.py build

WORKDIR /root

COPY tools tools
COPY siemens siemens
COPY plugins.yml plugins.yml

# === EXPERIMENTS ===

COPY common.sh .

COPY effectiveness.sh /usr/bin/effectiveness
RUN chmod +x /usr/bin/effectiveness

COPY scalability.sh /usr/bin/scalability
RUN chmod +x /usr/bin/scalability

# === DEBUGGING ===
RUN apt-get install -y vim less
