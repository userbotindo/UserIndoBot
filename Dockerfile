FROM userindobot/docker:ubotindo

# Clone Repo 
RUN git clone https://github.com/userbotindo/UserIndoBot.git -b master /app/userindo

# Wokrking Dir
WORKDIR /app/userindo/

# Copy Config To Working Dir
COPY ./config.py /app/userindo/ubotindo

# Run
CMD ["bash", "start"]
