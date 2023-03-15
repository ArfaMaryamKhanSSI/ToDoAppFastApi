FROM python:3.11

WORKDIR /app

#first copy req.txt so when we have a new package only then install all packages
COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

