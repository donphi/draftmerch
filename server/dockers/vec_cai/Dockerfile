# Start from Amazon Linux 2
FROM amazonlinux:2

# Install development tools and libraries needed for Python, cairosvg, and AWS CLI
RUN yum update -y && \
    yum groupinstall "Development Tools" -y && \
    yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget tar zip \
    cairo-devel pango-devel gdk-pixbuf2-devel libjpeg-devel openjpeg2-devel

# Download and install Python 3.10
RUN wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz && \
    tar -xzf Python-3.10.4.tgz && \
    cd Python-3.10.4 && \
    ./configure --enable-optimizations --with-ensurepip=install && \
    make altinstall

# Correcting the pip command to use pip3.10
RUN /usr/local/bin/pip3.10 install --upgrade pip && \
    /usr/local/bin/pip3.10 install awscli cairosvg

# Verify installation
RUN python3.10 --version && \
    pip3.10 --version && \
    python3.10 -m cairosvg --version

CMD ["/bin/bash"]
