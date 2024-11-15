# Stage 1: Compile Python, Install Dependencies, and Compile libpng16 from Source
FROM amazonlinux:2 AS python-build

# Prepare the build environment
RUN yum groupinstall -y "Development Tools" && \
    yum install -y tar openssl11-devel bzip2-devel libffi-devel zlib-devel wget shadow-utils.x86_64 zip \
    cairo-devel pango-devel gdk-pixbuf2-devel

# Example commands to install and verify libraries (adjust as necessary)
RUN yum install -y cairo pango gdk-pixbuf

# Then use find just to verify their presence (not for the final Dockerfile)
RUN find / -path /proc -prune -o -name libcairo.so.2 -print || echo "libcairo not found"
RUN find / -path /proc -prune -o -name libpango-1.0.so.0 -print || echo "libpango not found"

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
    LD_RUN_PATH=/usr/local/lib ./configure --enable-optimizations --enable-shared --with-ensurepip=install && \
    make altinstall

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

# Attempt to find and copy shared libraries to /opt/lib if they exist, searching the entire file system
RUN mkdir -p /opt/lib && \
    find / -path /proc -prune -o -name libpng16.so.16 -exec cp {} /opt/lib/ \; || : && \
    find / -path /proc -prune -o -name libcairo.so.2 -exec cp {} /opt/lib/ \; || : && \
    find / -path /proc -prune -o -name libpango-1.0.so.0 -exec cp {} /opt/lib/ \; || : && \
    find / -path /proc -prune -o -name libpangocairo-1.0.so.0 -exec cp {} /opt/lib/ \; || : && \
    find / -path /proc -prune -o -name libgdk_pixbuf-2.0.so.0 -exec cp {} /opt/lib/ \; || :

RUN ls -l /opt/lib/

# Ensure the system knows where to find the shared Python libraries and libpng16
RUN ldconfig /usr/local/lib

# Prepare the lambda layer zip file containing Python runtime, packages, and shared libraries
WORKDIR /lambda-layer
RUN mkdir -p python/lib/python3.10/site-packages/ && \
    cp -a /usr/local/lib/python3.10/site-packages/* python/lib/python3.10/site-packages/

# Ensure /opt/lib exists and copy the shared libraries there
RUN mkdir -p /opt/lib && \
    cp -a /opt/lib/* lib/ || : 

# Create the ZIP with the correct structure
RUN zip -r9 /lambda-layer.zip python /opt/lib

# Define a command to keep the container running, if necessary
CMD ["tail", "-f", "/dev/null"]


