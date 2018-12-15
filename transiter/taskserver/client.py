import rpyc


def refresh_tasks():
    try:
        conn = rpyc.connect('localhost', 12345)
        return conn.root.refresh_tasks()
    except ConnectionRefusedError:
        print('Could not connect to the Transiter task server')
    return False

