# Stage 1: Compile Python and Install Dependencies
FROM amazonlinux:2 AS python-build

# Install build essential tools
RUN yum groupinstall -y "Development Tools" && yum install -y \
  tar \
  openssl-devel \
  bzip2-devel \
  libffi-devel \
  zlib-devel \
  wget \
  shadow-utils.x86_64

# Install Python 3.10
WORKDIR /opt/python

ENV PYTHON_VERSION=3.10.4
RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar -xzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations --enable-shared --with-ensurepip=install && \
    make altinstall && \
    ldconfig

# Verify Python installation
RUN python3.10 --version
RUN pip3.10 --version

# Install cairosvg
RUN pip3.10 install cairosvg

# Stage 2: Prepare the runtime environment
FROM amazonlinux:2

# Copy the Python installation from the python-build stage
COPY --from=python-build /usr/local /usr/local

# Confirm Python3.10 is working
RUN python3.10 --version && pip3.10 --version

# Package for AWS Lambda
WORKDIR /lambda-layer
RUN mkdir python && \
    cd python && \
    cp -a /usr/local/lib/python3.10/site-packages/ . && \
    cp -a /usr/local/lib64/python3.10/site-packages/ . && \
    find . -name __pycache__ -exec rm -rf {} + && \
    cd .. && \
    zip -r9 /lambda-layer.zip .

# CMD to keep the container running if needed
CMD ["tail", "-f", "/dev/null"]