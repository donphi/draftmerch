# Start from Amazon Linux 2 base for AWS Lambda compatibility
FROM amazonlinux:2 as builder

# Define Python version for easy updates
ENV PYTHON_VERSION=3.10.4

# Install build dependencies for Python and libraries for cairosvg
RUN yum update -y && \
    yum groupinstall "Development Tools" -y && \
    yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget tar zip \
    cairo-devel pango-devel gdk-pixbuf2-devel libjpeg-devel openjpeg2-devel && \
    yum clean all

# Download and extract Python source
RUN cd /tmp && \
    wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz && \
    tar xvf Python-${PYTHON_VERSION}.tar.xz

# Compile Python with shared library support and optimize for size
RUN cd /tmp/Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib" && \
    make install

# Refresh shared library cache to ensure newly installed Python is found
RUN ldconfig

# Upgrade pip to latest version
RUN pip3 install --upgrade pip

# Install cairosvg and dependencies
RUN pip3 install cairosvg

# Prepare the layer packaging directory
RUN mkdir -p /lambda-layer/python/lib/python${PYTHON_VERSION::3}/site-packages
RUN cp -r /usr/local/lib/python${PYTHON_VERSION::3}/site-packages/* /lambda-layer/python/lib/python${PYTHON_VERSION::3}/site-packages/

# Final base to minimize size
FROM amazonlinux:2

# Copy the prepared Python libs to the final image to minimize size
COPY --from=builder /lambda-layer /lambda-layer

# Any additional layer preparation steps (permissions, etc) can be added here

# The instruction to package contents for AWS Lambda Layer
# Note: AWS Lambda expects the layer contents to be in a ZIP file in /opt directory
WORKDIR /lambda-layer
RUN zip -r /lambda-layer.zip .