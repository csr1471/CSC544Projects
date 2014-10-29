import sys, socket, re, time, Tkinter, tkFileDialog
import cPickle as pickle
from os import listdir, remove

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 1060

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
    server_dir = selectDirectory()
    
    # Establish Connection
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((hostname, port))
    s.listen(1)
    socket_conn, socket_addr = s.accept()

    # Initial Synchronization
    #-----------------------------------------------------------
    server_initial = [f for f in listdir(server_dir) if f[0]!='.']
    client_initial = pickle.loads(socket_conn.recv(8192))

    to_add_client = [f for f in server_initial if not f in client_initial]
    to_add_server = [f for f in client_initial if not f in server_initial]

    # Send needed files to client
    sendFiles(socket_conn, to_add_client, server_dir)


    # Receive needed files from client
    socket_conn.sendall(pickle.dumps(to_add_server))
    server_addition, num_files = pickle.loads(socket_conn.recv(16))  
    if server_addition:
        recvFiles(socket_conn, num_files, server_dir)

    print 'Synchronization complete.'


    # Server Sync Loop
    #-----------------------------------------------------------
    server_before = [f for f in listdir(server_dir) if f[0]!='.']
    client_before = pickle.loads(socket_conn.recv(8192))

    try:
        while(True):
            time.sleep(5)
            server_after = [f for f in listdir(server_dir) if f[0]!='.']
            client_after = pickle.loads(socket_conn.recv(8192))

            
            # Additions
            server_added = [f for f in server_after if not f in server_before]
            client_added = [f for f in client_after if not f in client_before]

            sendFiles(socket_conn, server_added, server_dir)

            socket_conn.sendall(pickle.dumps(client_added))
            server_addition, num_files = pickle.loads(socket_conn.recv(16))  
            if server_addition:
                recvFiles(socket_conn, num_files, server_dir)

            # Removals
            server_removed = [f for f in server_before if not f in server_after]
            client_removed = [f for f in client_before if not f in client_after]

            socket_conn.sendall(pickle.dumps(server_removed))
            
            if client_removed:
                for f in client_removed:
                    remove('/'.join([server_dir, f]))
                print 'Removed: ',','.join(client_removed)

            server_before = [f for f in listdir(server_dir) if f[0]!='.']
            client_before = pickle.loads(socket_conn.recv(8192))

    except (KeyboardInterrupt, EOFError, socket.error):
        pass

    s.close()
    print 'Connection closed.'
    
def iPyleClient(hostname):
    client_dir = selectDirectory()

    s.connect((hostname, port))

    # Initial Synchronization
    #-----------------------------------------------------------
    client_files = [f for f in listdir(client_dir) if f[0]!='.']
    s.sendall(pickle.dumps(client_files))

    # Receive needed files from server
    client_addition, num_files = pickle.loads(s.recv(16))
    if client_addition:
        recvFiles(s, num_files, client_dir)

    # Send needed files to server
    to_add_server = pickle.loads(s.recv(2097152))
    sendFiles(s, to_add_server, client_dir)

    print 'Synchronization complete.'

    # Client Sync Loop
    #-----------------------------------------------------------
    client_before = [f for f in listdir(client_dir) if f[0]!='.']
    s.sendall(pickle.dumps(client_before))

    
    try:
        while(True):
            time.sleep(5)
            client_after = [f for f in listdir(client_dir) if f[0]!='.']
            s.sendall(pickle.dumps(client_after))

            # Additions
            client_addition, num_files = pickle.loads(s.recv(16))
            if client_addition:
                recvFiles(s, num_files, client_dir)

            to_add_server = pickle.loads(s.recv(2097152))
            sendFiles(s, to_add_server, client_dir)

            # Removals
            to_remove_client = pickle.loads(s.recv(2097152))
            if to_remove_client:
                for f in to_remove_client:
                    remove('/'.join([client_dir, f]))
                print 'Removed: ',','.join(to_remove_client)

            # Refresh Directories
            client_before = [f for f in listdir(client_dir) if f[0]!='.']
            s.sendall(pickle.dumps(client_before))
            
    except (KeyboardInterrupt, EOFError, socket.error):
        pass
    
    s.close()
    print 'Connection closed.'

def selectDirectory():
    current_directory = Tkinter.Tk()
    directory_name = tkFileDialog.askdirectory(initialdir=current_directory, title='Select Folder...')
    current_directory.withdraw()
    print directory_name
    return directory_name


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
        print 'Added: ',','.join(file_list)
    else:
        sock.sendall(pickle.dumps([False, 0]))


def recvFiles(sock, n, directory):
    print directory
    for i in xrange(n):
        recv_file = pickle.loads(sock.recv(2097152))
        with open('{}/{}'.format(directory, recv_file['filename']), 'w') as f:
            f.write(recv_file['content'])

if __name__ == '__main__':
    main(sys.argv)
