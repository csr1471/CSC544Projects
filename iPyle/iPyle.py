import socket, sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = 12345

def main(args):
    HOST = args.pop() if len(args) == 3 else '127.0.0.1'
    if args[1:] == ['server']:
        iPyleServer(HOST)
    elif args[1:] == ['client']:
        iPyleClient(HOST)
    else:
        print 'Usage: python iPyle.py server|client [hostname]'

def iPyleServer(HOST):
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    print 'Listening on port', PORT
    s.listen(1)
    sc, sa = s.accept()
    print 'Connected to', sc.getpeername()[0]

    sc.close()
    print 'Connection closed'

def iPyleClient(HOST):
    s.connect((HOST, PORT))
    print 'Connected to {} on port {}'.format(HOST, s.getsockname()[1])
    s.close()
    print 'Connection closed.'

if __name__ == '__main__':
    main(sys.argv)
