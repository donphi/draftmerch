# Stage 1: Compile Python, Install Dependencies, and Compile libpng16 from Source
FROM amazonlinux:2 AS python-build

# Prepare the build environment
RUN yum groupinstall -y "Development Tools" && \
    yum install -y tar openssl11-devel bzip2-devel libffi-devel zlib-devel wget shadow-utils.x86_64 zip

# Compile libpng16 from source
WORKDIR /usr/src
RUN wget https://download.sourceforge.net/libpng/libpng-1.6.37.tar.gz && \
    tar -zxvf libpng-1.6.37.tar.gz && \
    cd libpng-1.6.37 && \
    ./configure --prefix=/usr/local && \
    make && make install

# Define the Python version
ENV PYTHON_VERSION=3.10.4

# Download and install Python from source
WORKDIR /opt/python
RUN wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz && \
    tar -xzf Python-$PYTHON_VERSION.tgz && \
    cd Python-$PYTHON_VERSION && \
    LD_RUN_PATH=/usr/lib64 ./configure --enable-optimizations --enable-shared --with-ensurepip=install && \
    make altinstall V=1

# Update ldconfig to know about Python 3.10 dynamic libraries and libpng16
RUN ldconfig /usr/local/lib

# Verify Python installation
RUN python3.10 --version && \
    pip3.10 --version

# Install cairosvg using pip
RUN pip3.10 install cairosvg

## Stage 2: Prepare the runtime environment
FROM amazonlinux:2

# Install zip and aws-cli
RUN yum update -y && \
    yum install -y zip aws-cli

# Copy necessary files from the build stage, including compiled Python and libpng16 libraries
COPY --from=python-build /usr/local /usr/local

# Update ldconfig to ensure the system knows where to find the shared Python libraries and libpng16
RUN ldconfig /usr/local/lib

# Verify that Python is correctly set up
RUN python3.10 --version && \
    pip3.10 --version

# Prepare the lambda layer zip file containing Python runtime and packages
WORKDIR /lambda-layer
RUN mkdir -p python && \
    cd python && \
    cp -a /usr/local/lib/python3.10/site-packages/ . && \
    if [ -d /usr/local/lib64/python3.10/site-packages/ ]; then cp -a /usr/local/lib64/python3.10/site-packages/ .; fi && \
    find . -name '__pycache__' -exec rm -rf {} + && \
    cd .. && \
    zip -r9 /lambda-layer.zip .

# Define a command to keep the container running, if necessary
CMD ["tail", "-f", "/dev/null"]
