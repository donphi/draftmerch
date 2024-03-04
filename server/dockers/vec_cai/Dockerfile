# Use Amazon Linux 2 as the base
FROM amazonlinux:2 as build-stage

# Install necessary packages
RUN yum update -y && \
    yum groupinstall -y "Development Tools" && \
    yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget tar zip \
    libjpeg-devel cairo-devel pango-devel gdk-pixbuf2-devel

# Install Python 3.10 from source to ensure compatibility with OpenSSL
RUN yum install -y gcc openssl-devel bzip2-devel libffi-devel && \
    cd /usr/src && \
    wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz && \
    tar xzf Python-3.10.4.tgz && \
    cd Python-3.10.4 && \
    ./configure --enable-optimizations && \
    make altinstall

# Verify Python 3.10 installation
RUN python3.10 --version

# Install pip for Python 3.10
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.10 get-pip.py

# Use pip to install cairosvg
RUN pip3.10 install cairosvg

# Create a directory for the lambda layer and copy necessary files
RUN mkdir -p /lambda-layer/python
RUN cp -r /usr/local/lib/python3.10 /lambda-layer/python/lib
RUN cp -r /usr/local/lib64/python3.10 /lambda-layer/python/lib64

# Prepare the zip file containing the layer
FROM amazonlinux:2 as final-stage
COPY --from=build-stage /lambda-layer /lambda-layer
WORKDIR /lambda-layer
RUN zip -r /python310-layer.zip .

# Final instructions to ensure when someone uses this image, they can easily extract the Lambda layer
CMD ["cp", "/lambda-layer/python310-layer.zip", "/target/python310-layer.zip"]