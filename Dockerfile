FROM ubuntu:16.04
  
MAINTAINER Toshiki Tsuboi <t.tsubo2000@gmail.com>

RUN apt-get update \
 && apt-get install -y git python-dev vim

WORKDIR /root
ADD https://bootstrap.pypa.io/get-pip.py /root
COPY . /root
RUN python get-pip.py \
 && pip install -r requirements.txt

COPY heat_mitaka/policy.json /etc/heat/
COPY nova_mitaka/policy.json /etc/nova/
