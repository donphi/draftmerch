# Start from Amazon Linux 2
FROM amazonlinux:2

# Install development tools and libraries needed for Python, cairosvg, and AWS CLI
RUN yum groupinstall "Development Tools" -y && \
    yum install -y \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    wget \
    tar \
    zip \
    cairo-devel \
    pango-devel \
    gdk-pixbuf2-devel \
    python3-pip

# Upgrade pip and install AWS CLI for S3 interactions
RUN pip3 install --upgrade pip && \
    pip3 install awscli

# Specify the exact Python 3.10 version to install
ENV PYTHON_VERSION=3.10.4

# Download and install Python 3.10
RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz && \
    tar xvf Python-${PYTHON_VERSION}.tar.xz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations && \
    make altinstall

# Cleanup
RUN rm -rf /usr/src/Python-${PYTHON_VERSION} /usr/src/Python-${PYTHON_VERSION}.tar.xz && \
    yum clean all

# Set Python 3.10 as the default python and pip version
RUN alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1 && \
    alternatives --set python3 /usr/local/bin/python3.10 && \
    alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.10 1

# Install cairosvg
RUN pip3.10 install cairosvg

# Verify installation
RUN python3 --version && pip --version && cairosvg --version
