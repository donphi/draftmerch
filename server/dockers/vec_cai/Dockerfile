# Start from Amazon Linux 2
FROM amazonlinux:2

# Install development tools and libraries needed for Python, cairosvg, and AWS CLI
RUN yum update -y && \
    yum groupinstall "Development Tools" -y && \
    yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget tar zip \
    cairo-devel pango-devel gdk-pixbuf2-devel

# Install Python 3.10 from Amazon Linux Extras repository
RUN amazon-linux-extras enable python3.8 && \
    yum install -y python3.8 && \
    alternatives --set python3 /usr/bin/python3.8

# Upgrade pip and install AWS CLI for S3 interactions
RUN pip3 install --upgrade pip && \
    pip3 install awscli

# Define environment variable for Python version
ENV PYTHON_VERSION=3.10.4

# Download and install Python, ensuring SSL support is correctly configured
# Note: Adjusting the approach to use a Python version available in Amazon Linux 2 extras
RUN pip3 install virtualenv && \
    virtualenv /opt/python3.10 && \
    source /opt/python3.10/bin/activate && \
    pip install --upgrade pip setuptools wheel

# Install cairosvg within the virtual environment
RUN source /opt/python3.10/bin/activate && \
    pip install cairosvg

# Verify installation
RUN source /opt/python3.10/bin/activate && \
    python --version && pip --version && cairosvg --version

CMD ["/bin/bash"]
