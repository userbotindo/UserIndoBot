# set base image (host OS)
FROM python:3.8

# set the working directory in the container
WORKDIR /ubotindo/

RUN apt -qq update && apt -qq upgrade
RUN apt -qq install -y --no-install-recommends \
    curl \
    git \
    gnupg2 \
    wget \

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY . .

# command to run on container start
CMD [ "bash", "./start" ]
