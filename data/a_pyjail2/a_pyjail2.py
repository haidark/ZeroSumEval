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

GREEN = '\033[92m'
WARNING = '\033[93m'
ERROR = '\033[91m'
ENDC = '\033[0m'

def main():
	text = input('>>> ')
	for keyword in ['eval', 'exec', 'import', 'open', 'os', 'read', 'system', 'write', 'subprocess']:
		if keyword in text:
			print(f"{ERROR}Nope, {WARNING}{keyword}{ERROR} is banned!{ENDC}")
			return
	exec(text)
	return


if __name__ == "__main__":
	print(f"{WARNING}Hi and welcome the most secure python console! Enter your commands.{ENDC}")
	print('-' * 80)
	while 1:
		try:
			main()
		except Exception as e:
			print(f"Oops, something broke: \n{ERROR}{e}{ENDC}")