FROM ubuntu:22.04

RUN apt-get update && apt-get install -y socat python3

RUN useradd -ms /bin/sh generated_pyjail
WORKDIR /home/generated_pyjail

COPY ./generated_pyjail.py ./
COPY ./flag.txt /

RUN chown -R root:generated_pyjail /home/generated_pyjail && \
     chmod 750 /home/generated_pyjail && \
     chmod 550 /home/generated_pyjail/generated_pyjail.py && \
     chown root:generated_pyjail /flag.txt && \
     chmod 440 /flag.txt

EXPOSE 31137

CMD ["socat", "-T60", "TCP-LISTEN:31137,reuseaddr,fork,su=generated_pyjail","EXEC:/home/generated_pyjail/generated_pyjail.py"]
