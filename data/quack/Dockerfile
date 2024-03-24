FROM debian:latest

RUN apt-get update -y && \
    apt-get install -y python3 openssh-server && \
    apt-get clean -y

RUN useradd -m user -s /bin/bash && \
    echo "user:pass" | chpasswd && \
    mkdir "/home/user/.secret"

COPY quack.py /home/user/quack.py
COPY flag.txt /home/user/.secret/flag.txt

WORKDIR /home/user

RUN chmod 444 /home/user/.secret/flag.txt && \
    chmod u+x /home/user/quack.py && \
    chown -R root:root /home/user

RUN echo "ForceCommand /home/user/quack.py" >> /etc/ssh/sshd_config && \
    mkdir /var/run/sshd

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]