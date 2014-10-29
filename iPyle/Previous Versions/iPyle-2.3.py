import sys, socket, re, time
import cPickle as pickle
from os import listdir, remove

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 1060

dir_name = './NetworkSync'

def main(args):
    # Use local host if IP address is not provided
    hostname = args.pop() if len(args) == 3 else '127.0.0.1'
    if args[1:] == ['server']:
        iPyleServer(hostname)
    elif args[1:] == ['client']:
        iPyleClient(hostname)
    else:
        print 'usage: iPyle.py server|client [host]'

def iPyleServer(hostname):   
    # Establish Connection
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((hostname, port))
    s.listen(1)
    socket_conn, socket_addr = s.accept()

    # Initial Synchronization
    #-----------------------------------------------------------
    server_initial = [f for f in listdir(dir_name) if f[0]!='.']
    client_initial = pickle.loads(socket_conn.recv(8192))

    to_add_client = [f for f in server_initial if not f in client_initial]
    to_add_server = [f for f in client_initial if not f in server_initial]

    # Send needed files to client
    sendFiles(socket_conn, to_add_client)

    # Receive needed files from client
    socket_conn.sendall(pickle.dumps(to_add_server))
    server_addition, num_files = pickle.loads(socket_conn.recv(8192))
    if server_addition:
        recvFiles(socket_conn, num_files)

    print 'Synchronization complete.'


    # Server Sync Loop
    #-----------------------------------------------------------
    server_before = [f for f in listdir(dir_name) if f[0]!='.']
    client_before = pickle.loads(socket_conn.recv(8192))

    try:
        while(True):
            time.sleep(5)
            server_after = [f for f in listdir(dir_name) if f[0]!='.']
            client_after = pickle.loads(socket_conn.recv(8192))

            
            # Additions
            server_added = [f for f in server_after if not f in server_before]
            client_added = [f for f in client_after if not f in client_before]

            sendFiles(socket_conn, server_added)

            socket_conn.sendall(pickle.dumps(client_added))
            client_added, num_files = pickle.loads(socket_conn.recv(8192))  
            if client_added:
                recvFiles(socket_conn, num_files)

            # Removals
            server_removed = [f for f in server_before if not f in server_after]
            client_removed = [f for f in client_before if not f in client_after]

            socket_conn.sendall(pickle.dumps(server_removed))
            
            if client_removed:
                for f in client_removed:
                    remove('/'.join([dir_name, f]))
                print 'Removed: ',','.join(client_removed)

            server_before = [f for f in listdir(dir_name) if f[0]!='.']
            client_before = pickle.loads(socket_conn.recv(8192))

    except (KeyboardInterrupt, EOFError, socket.error):
        pass

    s.close()
    print 'Connection closed.'
    
def iPyleClient(hostname):
    s.connect((hostname, port))

    # Initial Synchronization
    #-----------------------------------------------------------
    client_initial = [f for f in listdir(dir_name) if f[0]!='.']
    s.sendall(pickle.dumps(client_initial))

    # Receive needed files from server
    client_addition, num_files = pickle.loads(s.recv(8192))
    if client_addition:
        recvFiles(s, num_files)

    # Send needed files to server
    to_add_server = pickle.loads(s.recv(8192))
    sendFiles(s, to_add_server)

    print 'Synchronization complete.'

    # Client Sync Loop
    #-----------------------------------------------------------
    client_before = [f for f in listdir(dir_name) if f[0]!='.']
    s.sendall(pickle.dumps(client_before))

    
    try:
        while(True):
            time.sleep(5)
            client_after = [f for f in listdir(dir_name) if f[0]!='.']
            s.sendall(pickle.dumps(client_after))

            # Additions
            server_added, num_files = pickle.loads(s.recv(8192))
            if server_added:
                recvFiles(s, num_files)

            client_added = pickle.loads(s.recv(8192))
            sendFiles(s, client_added)

            # Removals
            server_removed = pickle.loads(s.recv(8192))
            print server_removed
            if server_removed:
                for f in server_removed:
                    remove('/'.join([dir_name, f]))
                print 'Removed: ',','.join(to_remove_client)

            # Refresh Directories
            client_before = [f for f in listdir(dir_name) if f[0]!='.']
            s.sendall(pickle.dumps(client_before))
            
    except (KeyboardInterrupt, EOFError, socket.error):
        pass
    
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


def sendFiles(sock, file_list):
    if file_list:
        sock.sendall(pickle.dumps([True, len(file_list)]))
        for f in file_list:
            sock.sendall(formatFile('{}/{}'.format(dir_name, f)))
        print 'Added: ',','.join(file_list)
    else:
        sock.sendall(pickle.dumps([False, 0]))


def recvFiles(sock, n):
    for i in xrange(n):
        recv_file = pickle.loads(sock.recv(8192))
        with open('{}/{}'.format(dir_name, recv_file['filename']), 'w') as f:
            f.write(recv_file['content'])

if __name__ == '__main__':
    main(sys.argv)
