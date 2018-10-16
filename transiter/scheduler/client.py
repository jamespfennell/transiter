"""
Have a very simply refresh_jobs functions
that makes the connection, and hits the correct function in the server

"""

import rpyc


def refresh_jobs():
    try:
        conn = rpyc.connect('localhost', 12345)
        return conn.root.refresh_jobs()
    except ConnectionRefusedError:
        print('Could not connect to the RPyC scheduler service')
    return False

