# Start from Amazon Linux 2
FROM amazonlinux:2

# Install development tools and libraries needed for Python and cairosvg
RUN yum update -y && \
    yum groupinstall "Development Tools" -y && \
    yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget tar zip \
    cairo-devel pango-devel gdk-pixbuf2-devel libjpeg-devel openjpeg2-devel

# Download and install Python 3.10
RUN wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz && \
    tar -xzf Python-3.10.4.tgz && \
    cd Python-3.10.4 && \
    ./configure --enable-optimizations --with-ensurepip=install && \
    make altinstall && \
    cd .. && rm -rf Python-3.10.4 Python-3.10.4.tgz

# Update alternatives to use Python 3.10
RUN update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1 && \
    update-alternatives --set python3 /usr/local/bin/python3.10

# Upgrade pip and install AWS CLI for S3 interactions
RUN pip3 install --upgrade pip && \
    pip3 install awscli

# Install cairosvg
RUN pip3 install cairosvg

# Verify installation
RUN python3 --version && pip3 --version && cairosvg --version

CMD ["/bin/bash"]
