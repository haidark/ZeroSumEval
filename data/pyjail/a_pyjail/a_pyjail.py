#!/usr/bin/env python3

# Pwn mostly builds on top of rev.
# While rev is more about understanding how a program works, pwn is more about figuring out how to exploit a program to reach the holy grail: Arbitrary Code Execution
#
# If you can execute arbitrary code on a system, that system might as well be yours...because you can do whatever you want with it! (this is the namesake of "pwn".....if you pwn a system, you own the system)
# Of course, that comes with the limitations of the environment you are executing code in...are you a restricted user, or a super admin?
# Sometimes you can make yourself a super admin starting from being a restricted user.....but we're not gonna do that right now.
#
# For now, I want you to figure out how to execute arbitrary commands on the server running the following code.
#
# To prove to me that you can excute whatever commands you want on the server, you'll need to get the contents of `/flag.txt`

blacklist = ['write','open','pty','from','sys','platform','type', 'ls', 'cat', 'flag', 'head', 'tail']
import os

while True:
	cmd = input(">>> ")
	if any([x in cmd  for x in blacklist]):
		print ("did not pass filter")
		pass
	else:
		try:
			print(cmd)
			exec(cmd)
		except Exception as e :
			print(f"error running command\n{e}")
			pass