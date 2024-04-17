FROM ubuntu:22.04

RUN apt-get update && apt-get install -y socat python3

RUN useradd -ms /bin/sh a_pyjail
WORKDIR /home/a_pyjail

COPY ./a_pyjail ./
COPY ./flag.txt /

RUN chown -R root:a_pyjail /home/a_pyjail && \
     chmod 750 /home/a_pyjail && \
     chmod 550 /home/a_pyjail/a_pyjail && \
     chown root:a_pyjail /flag.txt && \
     chmod 440 /flag.txt

EXPOSE 31137

CMD ["socat", "-T60", "TCP-LISTEN:31137,reuseaddr,fork,su=a_pyjail","EXEC:/home/a_pyjail/a_pyjail"]
