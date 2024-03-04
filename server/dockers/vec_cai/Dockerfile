# Use Amazon Linux 2 as the base image
FROM amazonlinux:2

# Install development tools and dependencies required for building Python
RUN yum groupinstall -y "Development Tools" && \
    yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget tar zip \
    cairo-devel pango-devel gdk-pixbuf2-devel

# Download and install Python 3.10, ensuring SSL support is correctly configured
RUN wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz && \
    tar -xzf Python-3.10.4.tgz && \
    cd Python-3.10.4 && \
    ./configure --enable-optimizations --with-ensurepip=install --with-openssl=/usr/include/openssl && \
    make altinstall

# Cleanup to reduce image size
RUN yum clean all && \
    rm -rf /var/cache/yum /Python-3.10.4.tgz /Python-3.10.4

# Upgrade pip to the latest version
RUN /usr/local/bin/pip3.10 install --upgrade pip

# Install AWS CLI and cairosvg using the newly installed pip
RUN /usr/local/bin/pip3.10 install awscli cairosvg

# Verify installation
RUN python3.10 --version && pip3.10 --version && python3.10 -m cairosvg --version

CMD ["/bin/bash"]
