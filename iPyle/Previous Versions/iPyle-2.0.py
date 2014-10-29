import sys, socket, re
import cPickle as pickle
from os import listdir

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 1060

def main(args):
    hostname = args.pop() if len(args) == 3 else '127.0.0.1'
    if args[1:] == ['server']:
        iPyleServer(hostname)
    elif args[1:] == ['client']:
        iPyleClient(hostname)
    else:
        print 'usage: iPyle.py server|client [host]'

def iPyleServer(hostname):
    s.bind((hostname, port))
    s.listen(1)
    socket_conn, socket_addr = s.accept()

    server_dir = './Server'

    server_before = [f for f in listdir(server_dir) if f[0]!='.']
    client_before = pickle.loads(socket_conn.recv(8192))

    to_add_client = [f for f in server_before if not f in client_before]
    to_add_server = [f for f in client_before if not f in server_before]

    sendFiles(socket_conn, to_add_client, server_dir)
    socket_conn.sendall(pickle.dumps(to_add_server))

    server_addition, num_files = pickle.loads(socket_conn.recv(16))
    
    if server_addition:
        recvFiles(socket_conn, num_files, server_dir)

    s.close()
    print 'Connection closed.'

def iPyleClient(hostname):
    s.connect((hostname, port))
    
    client_dir = './Client'
    
    client_files = [f for f in listdir(client_dir) if f[0]!='.']
    s.sendall(pickle.dumps(client_files))

    client_addition, num_files = pickle.loads(s.recv(16))
    if client_addition:
        recvFiles(s, num_files, directory)

    to_add_server = pickle.loads(s.recv(2097152))
    sendFiles(s, to_add_server, client_dir)

    
    s.close()
    print 'Connection closed.'

def formatFile(filename):
    with open(filename, 'r') as f:
        match = re.search('(.+)/(.+)', f.name)
        if match:
            file_path = match.group(1)
            file_name = match.group(2)
        file_content = f.read()

    file_data = {
        'filename': file_name,
        'content': file_content
    }
    return pickle.dumps(file_data)

def sendFiles(sock, file_list, directory):
    if file_list:
        sock.sendall(pickle.dumps([True, len(file_list)]))
        for f in file_list:
            sock.sendall(formatFile('{}/{}'.format(directory, f)))
    else:
        sock.sendall(pickle.dumps([False, 0]))

def recvFiles(sock, n, directory):
    for i in xrange(n):
        recv_file = pickle.loads(sock.recv(2097152))
        with open('{}/{}'.format(directory, recv_file['filename']), 'w') as f:
            f.write(recv_file['content'])

if __name__ == '__main__':
    main(sys.argv)
