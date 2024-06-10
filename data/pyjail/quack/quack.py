#!/usr/bin/env python3
import readline
import code
from traceback import print_exc
from sys import exit

print("""
A sleepy duck is blocking the way to my files. 
Can you wake it up (gently) and ask it for 
flag.txt? Thanks!
    __
___( -)>
\ <_. )
 `---'   hjw
""")

try:
    while True:
        input("> ")
except KeyboardInterrupt:
    exit()
except EOFError:
    print("""
    __
___( O)>
\ <_. )
 `---'   hjw
""")
    print_exc()
    code.InteractiveConsole(globals()).interact(banner="",exitmsg="")