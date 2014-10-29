import sys, socket

s = socket.socket(socket.AF_INET, socket.SOCK_STEAM)
PORT = 1060

def main(args):
    HOST = args.pop() if len(args) == 3 else '127.0.0.1'
    if args[1:] == 'server':
        iPyleServer()
    elif args[1:] == 'client':
        iPyleClient()
    else:
        print >> sys.stderr, 'usage: iPyle.py server|client [host]'

if __name__ == '__main__':
    main(sys.argv)
