FROM python:latest

WORKDIR /home
COPY a_pyjail3.py .
COPY flag.txt .
RUN chmod +x ./jail.py

#RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN apt update && apt install -y socat

CMD socat tcp-listen:13370,reuseaddr exec:"a_pyjail3"
#CMD /usr/bin/python /home/jail.py