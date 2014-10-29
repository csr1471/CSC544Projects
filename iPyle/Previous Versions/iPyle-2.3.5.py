import socket, sys
import cPickle as pickle
from os import listdir

dir_name = './NetworkSync'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = sys.argv.pop() if len(sys.argv) == 3 else '127.0.0.1'
PORT = 12345

def main(args):
    if args[1:] == ['server']:
        iPyleServer()
    elif args[1:] == ['client']:
        iPyleClient()
    else:
        print 'Usage: python iPyle.py client|server [host]'

def iPyleServer():
    # Establish Connection
    #-----------------------------------------------------------
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    print 'Listening on port {}.'.format(PORT)
    s.listen(1)
    sc, sa = s.accept()
    client_addr, client_port = sc.getpeername()
    print 'Connected to {} on port {}.'.format(client_addr, PORT)

    # Initial Synchronization
    #-----------------------------------------------------------
    server_initial = [f for f in listdir(dir_name) if f[0]!='.']
    print 'Asking for client file list...',
    client_initial = pickle.loads(sc.recv(8192))
    print 'Received!'

    to_add_client = [f for f in server_initial if not f in client_initial]
    to_add_server = [f for f in client_initial if not f in server_initial]

    print 'Sending client missing list size.'
    sc.sendall(pickle.dumps(len(to_add_client)))
    if len(to_add_client) > 0:
        print 'Sending missing files to client...',
        for f in to_add_client:
            sc.sendall(formatFile(f))
        print 'sent.'
    

    # Close Connection
    #-----------------------------------------------------------
    sc.close()
    print 'Connection closed.'

def iPyleClient():
    # Establish Connection
    #-----------------------------------------------------------
    s.connect((HOST, PORT))
    client_addr, client_port = s.getsockname()
    print 'Connected to {}:{} on port {}.'.format(HOST, PORT, client_port)

    # Initial Synchronization
    #-----------------------------------------------------------
    print 'Sending file list to server...',
    client_initial = [f for f in listdir(dir_name) if f[0]!='.']
    s.sendall(pickle.dumps(client_initial))
    print 'Sent!'

    print 'Receiving missing list size...',
    num_files = pickle.loads(s.recv(8192))
    print 'Done!'

    if num_files > 0:
        print 'Receiving missing files...',
        for i in range(num_files):
            recv_file = pickle.loads(s.recv(8192))
            with open('{}/{}'.format(dir_name, recv_file['filename']), 'w') as f:
                f.write(recv_file['content'])
            print recv_file['filename'],
        print 'received.'
    

    # Close Connection
    #-----------------------------------------------------------
    s.close()
    print 'Connection closed.'

def formatFile(file_name):
    with open('{}/{}'.format(dir_name, file_name), 'r') as f:
        file_content = f.read()

    file_data = {
        'filename': file_name,
        'content': file_content
    }

    return pickle.dumps(file_data)

if __name__ == '__main__':
    main(sys.argv)
