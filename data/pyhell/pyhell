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

import re
import builtins
import sys

def safe_eval(user_input):
    safe_builtins = {
        "__builtins__": {name: getattr(builtins, name) for name in ['print', 'int', 'float', '__import__', 'getattr', 'chr']}
    }

    try:
        exec(user_input, safe_builtins, {})
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def jail():
    ascii_art = """
                                                                                                        _..._                                  
                                .---..---.                                                           .-'_..._''.                    .---..---. 
   .              __.....__     |   ||   |          .--.   _..._                                   .' .'      '.\\     __.....__     |   ||   | 
 .'|          .-''         '.   |   ||   |          |__| .'     '.                                / .'            .-''         '.   |   ||   | 
<  |         /     .-''"'-.  `. |   ||   |          .--..   .-.   .                              . '             /     .-''"'-.  `. |   ||   | 
 | |        /     /________\\   \\|   ||   |          |  ||  '   '  |              __              | |            /     /________\\   \\|   ||   | 
 | | .'''-. |                  ||   ||   |          |  ||  |   |  |           .:--.'.            | |            |                  ||   ||   | 
 | |/.'''. \\\\    .-------------'|   ||   |          |  ||  |   |  |          / |   \\ |           . '            \\\\    .-------------'|   ||   | 
 |  /    | | \\    '-.____...---.|   ||   |          |  ||  |   |  |          `" __ | |            \\ '.          .\\    '-.____...---.|   ||   | 
 | |     | |  `.             .' |   ||   |          |__||  |   |  |           .'.''| |             '. `._____.-'/ `.             .' |   ||   | 
 | |     | |    `''-...... -'   '---''---'              |  |   |  |          / /   | |_              `-.______ /    `''-...... -'   '---''---' 
 | '.    | '.                                           |  |   |  |          \\ \\._,\\ '/                       `                                
 '---'   '---'                                          '--'   '--'           `--'  `"                                                         
!! Even Michael Scofield can not escape this .
    """
    print(ascii_art)

    max_input_length = 553

    while True:
        user_input = input(">>> ")

        if len(user_input) > max_input_length:
            print("Bro chill !!! That's kinda long")
            continue

        blacklist = ['exec', 'eval', 'os', 'sys', 'subprocess', 'file', 'open', 'register', 'setattr', 'input', 'mro', 'globals', 'class', 'getitem', 'breakpoint', '_', '.','[',']']

        for block in blacklist:
            if block in user_input:
                print(f"No no {block} is not allowed in here")
                break
        else:
            safe_eval(user_input)

if __name__ == "__main__":
    jail()