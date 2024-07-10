import subprocess


def submit_solution():
    pass


def print_verbose(message, verbose):
    if verbose:
        print(message)


def verify_solution(soln, verbose=False):
    """ verify the solution to the challenge """
    output = ""
    # soln = b"""open("/flag.txt", 'r').read()"""
    # soln = b"""'password'"""
    netcat_cmd = f"nc localhost 31137"
    nc_process = subprocess.Popen(
        netcat_cmd.split(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Read the server's first output
    initial_output = nc_process.stdout.read(1)
    output += initial_output.decode()
    # Send the solution to the server
    nc_process.stdin.write(soln.encode() + b"\n")
    nc_process.stdin.flush()
    # Read the server's response
    response = nc_process.stdout.read()
    output += response.decode()
    print_verbose(output, verbose)
    if "csawctf{neigh______}" in output:
        return True
    else:
        return False
