FROM ubuntu:22.04

RUN apt-get update && apt-get install -y socat python3

RUN useradd -ms /bin/sh pyhell
WORKDIR /home/pyhell

COPY ./pyhell ./
COPY ./flag.txt /

RUN chown -R root:pyhell /home/pyhell && \
     chmod 750 /home/pyhell && \
     chmod 550 /home/pyhell/pyhell && \
     chown root:pyhell /flag.txt && \
     chmod 440 /flag.txt

EXPOSE 31137

CMD ["socat", "-T60", "TCP-LISTEN:31137,reuseaddr,fork,su=pyhell","EXEC:/home/pyhell/pyhell"]
