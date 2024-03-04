# Start from Amazon Linux 2
FROM amazonlinux:2

# Install development tools and libraries needed for Python and cairosvg
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
    gdk-pixbuf2-devel

# Download Python 3.10, replace x with the minor version you need
RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/3.10.x/Python-3.10.x.tar.xz && \
    tar xvf Python-3.10.x.tar.xz

# Compile Python 3.10
RUN cd /usr/src/Python-3.10.x && \
    ./configure --enable-optimizations && \
    make altinstall

# Cleanup
RUN rm /usr/src/Python-3.10.x.tar.xz && \
    yum clean all

# Set Python 3.10 as the default python and pip version
RUN alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1 && \
    alternatives --set python3 /usr/local/bin/python3.10 && \
    alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.10 1

# Install cairosvg
RUN pip3.10 install cairosvg

# Verify installation
RUN python3 --version && pip --version && cairosvg --version
