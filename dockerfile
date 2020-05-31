FROM python:3.7

# Create app directory
WORKDIR /app

# Install app dependencies
COPY requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY gunicorn_app /app

EXPOSE 8080
