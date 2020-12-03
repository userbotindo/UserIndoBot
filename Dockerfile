FROM userindobot/docker:ubotindo

RUN apt -qq update -y

# Wokrking Dir
WORKDIR /app/userindo/

# requirements setup
COPY requirements.txt .

RUN pip install -U pip
RUN pip install -r requirements.txt

# Copy All resources
COPY . .

# set env path
ENV PATH="/home/bot/bin:$PATH"

# Run
CMD ["python3", "-m", "ubotindo"]
