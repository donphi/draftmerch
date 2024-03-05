# Stage 1: Compile Python and Install Dependencies
FROM amazonlinux:2 AS python-build

# Prepare the build environment
RUN yum groupinstall -y "Development Tools" && \
    yum install -y tar openssl-devel bzip2-devel libffi-devel zlib-devel wget shadow-utils.x86_64

# List installed openssl packages and locate libssl
RUN yum list installed | grep openssl
RUN find / -name libssl.so*

# Define the Python version
ENV PYTHON_VERSION=3.10.4

# Download and install Python from source
WORKDIR /opt/python
RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar -xzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations --enable-shared --with-ensurepip=install --with-openssl=/usr/local/ssl && \
    make altinstall

# Update ldconfig to know about Python 3.10 dynamic libraries
RUN ldconfig /usr/local/lib

# Verify Python installation
RUN python3.10 --version && \
    pip3.10 --version

# Install cairosvg using pip
RUN pip3.10 install cairosvg

# Stage 2: Prepare the runtime environment
FROM amazonlinux:2

# Copy necessary files from the build stage
COPY --from=python-build /usr/local /usr/local

# Update ldconfig to ensure the system knows where to find the shared Python libraries
RUN ldconfig /usr/local/lib

# Verify that Python is correctly set up
RUN python3.10 --version && \
    pip3.10 --version

# Prepare the lambda layer zip file containing Python runtime and packages
WORKDIR /lambda-layer
RUN mkdir -p python && \
    cd python && \
    cp -a /usr/local/lib/python3.10/site-packages/ . && \
    cp -a /usr/local/lib64/python3.10/site-packages/ . && \
    find . -name '__pycache__' -exec rm -rf {} + && \
    cd .. && \
    zip -r9 /lambda-layer.zip .

# Define a command to keep the container running, if necessary
CMD ["tail", "-f", "/dev/null"]