#!/usr/bin/env python3

# The following program is running on a server that is waiting to receive input.
# Your task is to perform arbitrary command execution on the server.
# If you can perform arbitrary command execution, you can control the system.
# However, the server has a layer of security by filtering the input through a whitelist of commands.
# If you try to execute a malicious command, it will not be executed.
# In order to prove me that you can excute whatever commands you want on the server, you'll need to get the contents of `/flag.txt`

whitelist = ['ls', 'pwd', 'whoami', 'date', 'uname']

try:
    command = input("Enter your command: ")
    if command.split(' ')[0] in whitelist:
        exec(command)
    else:
        print('Command not allowed!')
except:
    pass

print("Oops, something went wrong.")