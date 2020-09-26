FROM python:3.8

# Set Working Directory
WORKDIR /app/
#
# Installing Packages
#
RUN apt update && apt upgrade -y && \
    apt install --no-install-recommends -y \
    bash \
    git \
    libffi-dev \
    libjpeg-dev \
    libxslt1-dev \
    gcc \
    && rm -rf /var/lib/apt/lists /var/cache/apt/archives /tmp

# Pypi package Repo upgrade
RUN pip3 install --upgrade pip setuptools

# Copy Requirements To Working Dir
COPY requirements.txt .

# Install requirements
RUN pip3 install -U -r requirements.txt

# Starting Worker
CMD ["python3","-m","ubotindo"]
