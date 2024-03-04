# Use Ubuntu as the base image
FROM ubuntu:latest

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Update and install development tools and required libraries
RUN apt-get update && \
    apt-get install -y build-essential libffi-dev zlib1g-dev \
    libbz2-dev libncurses5-dev libreadline-dev libsqlite3-dev libssl-dev \
    libgdbm-dev libnss3-dev libsm6 libxrender1 libfontconfig1 libxext6 \
    tk-dev liblzma-dev libdb-dev libpcap-dev xz-utils wget curl libcairo2-dev \
    libpango1.0-dev libgdk-pixbuf2.0-dev libxml2-dev libxslt-dev zip unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

# Download Python 3.10.4 source
RUN curl -O https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tar.xz

# Extract and compile Python from source
RUN tar -xf Python-3.10.4.tar.xz && \
    cd Python-3.10.4 && \
    ./configure --enable-optimizations --with-ensurepip=install && \
    make -j 8 altinstall && \
    cd .. && \
    rm -rf Python-3.10.4 Python-3.10.4.tar.xz

# Verify Python Version
RUN python3.10 --version

# Set Python 3.10 as the default python version if needed
RUN update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1 && \
    update-alternatives --set python3 /usr/local/bin/python3.10

# Creating a work directory for your application
WORKDIR /app

# Copying your application source code and requirements.txt into the Docker image
COPY requirements.txt .

# Upgrade pip and install Python dependencies specified in requirements.txt
RUN python3.10 -m pip install --upgrade pip && \
    python3.10 -m pip install -r requirements.txt
