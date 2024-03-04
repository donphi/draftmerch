# Start from Amazon Linux 2
FROM amazonlinux:2

# Install development tools and libraries needed for Python, cairosvg, and AWS CLI
RUN yum update -y && \
    yum groupinstall "Development Tools" -y && \
    yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget tar zip \
    cairo-devel pango-devel gdk-pixbuf2-devel python3-pip

# Upgrade pip and install AWS CLI for S3 interactions
RUN pip3 install --upgrade pip && \
    pip3 install awscli

# Define environment variable for Python version
ENV PYTHON_VERSION=3.10.4

# Download and install Python, ensuring SSL support is correctly configured
# Note: You may need to adjust the --with-openssl flag if the path is different
RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz && \
    tar xvf Python-${PYTHON_VERSION}.tar.xz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations --with-ensurepip=install --with-openssl=/usr/include/openssl && \
    make altinstall

# Cleanup to reduce image size
RUN yum clean all && \
    rm -rf /var/cache/yum /usr/src/Python-${PYTHON_VERSION}

# Set Python 3.10 as the default python and pip version
RUN alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1 && \
    alternatives --set python3 /usr/local/bin/python3.10 && \
    alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.10 1

# Install cairosvg
RUN pip3.10 install cairosvg

# Verify installation
RUN python3.10 --version && pip3.10 --version && cairosvg --version
