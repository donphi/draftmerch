FROM amazonlinux:2

RUN yum update -y \
    && yum install -y tar gzip make gcc openssl-devel bzip2-devel libffi-devel wget \
    && yum clean all

RUN cd /usr/src \
    && wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz \
    && tar xzf Python-3.10.4.tgz \
    && cd Python-3.10.4 \
    && ./configure --enable-optimizations \
    && make altinstall \
    && rm -f /usr/src/Python-3.10.4.tgz

RUN python3.10 --version
