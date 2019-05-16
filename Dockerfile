FROM ubuntu:latest

MAINTAINER Paul Charbonneau "paulcharbo@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

WORKDIR /
COPY . /
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]

CMD [ "server.py" ]