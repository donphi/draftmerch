FROM amazonlinux:2

# Install development tools and required libraries (including openssl-devel for SSL support in Python)
RUN yum -y update && \
    yum groupinstall -y "Development Tools" && \
    yum install -y libffi-devel zlib-devel bzip2-devel \
    ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel \
    libpcap-devel xz-devel openssl-devel && \
    yum clean all

# Download Python 3.10.4 source
RUN curl -O https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tar.xz

# Extract and compile Python from source
RUN tar -xf Python-3.10.4.tar.xz && \
    cd Python-3.10.4 && \
    ./configure --prefix=/usr --enable-optimizations --with-ensurepip=install --with-openssl=/usr/include/openssl && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.10.4 Python-3.10.4.tar.xz

# Verify Python Version
RUN python3.10 --version

# Install cairo, pango for cairosvg
RUN yum install -y cairo pango gdk-pixbuf

# Set Python 3.10 as the default python version using alternatives
RUN alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1 && \
    alternatives --set python3 /usr/local/bin/python3.10

# Creating a work directory for your application
WORKDIR /app

# Copying your application source code and requirements.txt into the Docker image
COPY . .

# Upgrade pip and install Python dependencies specified in requirements.txt
RUN python3.10 -m pip install --upgrade pip && \
    python3.10 -m pip install -r requirements.txt
