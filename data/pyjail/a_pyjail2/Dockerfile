FROM python:latest

WORKDIR /home
COPY jail.py .
COPY flag.txt .
RUN chmod +x ./jail.py

#RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN apt update && apt install -y socat

CMD socat tcp-listen:13370,reuseaddr exec:"python jail.py"
#CMD /usr/bin/python /home/jail.py