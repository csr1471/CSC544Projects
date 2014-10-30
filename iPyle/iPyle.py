import socket, sys, time
import cPickle as pickle
from os import listdir

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = 12345
SIZE_BUFF = 8

dir_name = 'NetworkSync'

def main(args):
    HOST = args.pop() if len(args) == 3 else '127.0.0.1'
    if args[1:] == ['server']:
        iPyleServer(HOST)
    elif args[1:] == ['client']:
        iPyleClient(HOST)
    else:
        print 'Usage: python iPyle.py server|client [hostname]'

def iPyleServer(HOST):
    # Remove when working
    global dir_name
    dir_name = 'C:\Users\Callie\Desktop\NetworkSync_Server'
    
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    print 'Listening...',
    s.listen(1)
    sc, sa = s.accept()
    print 'connected to {} on port {}'.format(sc.getpeername()[0], PORT)

    

    # Initial Sync
    server_files = [f for f in listdir(dir_name) if f[0]!='.']
    print 'Receiving client file list...',
    length = recv_all(sc, SIZE_BUFF)
    client_files = pickle.loads(recv_all(sc, int(length)))
    print 'done.'

    to_add_server = [f for f in client_files if not f in server_files]
    to_add_client = [f for f in server_files if not f in client_files]

    send_all(sc, to_add_server)

    if to_add_server:
        print 'Receiving files from server...',
        for f in to_add_server:
            length = recv_all(sc, SIZE_BUFF)
            recv_file = pickle.loads(recv_all(sc, int(length)))
            with open('{}/{}'.format(dir_name, recv_file['name']), 'w') as f:
                f.write(recv_file['content'])
        print 'done.'

    send_all(sc, to_add_client)
    
    if to_add_client:
        print 'Sending files to client...',
        for f in to_add_client:
            send_all(sc, formatFile(f))
        print 'done.'
    print 'Initial sync complete!'

    

    # Server continuous sync loop
    server_before = client_before = [f for f in listdir(dir_name) if f[0]!='.']

    while (True):
        time.sleep(5)
        server_after = [f for f in listdir(dir_name) if f[0]!='.']
        print 'Receiving client updates...',
        length = recv_all(sc, SIZE_BUFF)
        client_after = pickle.loads(recv_all(sc, int(length)))
        print 'done.'

        server_additions = [f for f in server_after if not f in server_before]
        client_additions = [f for f in client_after if not f in client_before]

        send_all(sc, client_additions)

        if client_additions:
            print 'Receiving files from server...',
            for f in client_additions:
                length = recv_all(sc, SIZE_BUFF)
                recv_file = pickle.loads(recv_all(sc, int(length)))
                with open('{}/{}'.format(dir_name, recv_file['name']), 'w') as f:
                    f.write(recv_file['content'])
            print 'done.'

        send_all(sc, server_additions)
        
        if server_additions:
            print 'Sending files to client...',
            for f in server_additions:
                send_all(sc, formatFile(f))
            print 'done.'

        print 'Refreshing folder lists...',
        server_before = [f for f in listdir(dir_name) if f[0]!='.']
        length = recv_all(sc, SIZE_BUFF)
        client_before = pickle.loads(recv_all(sc, int(length)))
        print 'done.'

    sc.close()
    print 'Connection closed.'

def iPyleClient(HOST):
    # Remove when working
    global dir_name
    dir_name = 'C:\Users\Callie\Desktop\NetworkSync_Client'

    print 'Establishing a connection...',
    s.connect((HOST, PORT))
    print 'connected to {} on port {}'.format(HOST, s.getsockname()[1])


    # Initial Sync    
    print 'Sending client file list...',
    client_files = [f for f in listdir(dir_name) if f[0]!='.']
    send_all(s, client_files)
    print 'done.'

    length = recv_all(s, SIZE_BUFF)
    to_add_server = pickle.loads(recv_all(s, int(length)))
    if to_add_server:
        print 'Sending files to server...',
        for f in to_add_server:
            send_all(s, formatFile(f))
        print 'done.'
    
    
    length = recv_all(s, SIZE_BUFF)
    to_add_client = pickle.loads(recv_all(s, int(length)))
    if to_add_client:
        print 'Receiving files from server...',
        for f in to_add_client:
            length = recv_all(s, SIZE_BUFF)
            recv_file = pickle.loads(recv_all(s, int(length)))
            with open('{}/{}'.format(dir_name, recv_file['name']), 'w') as f:
                f.write(recv_file['content'])
        print 'done.'
    print 'Initial sync complete!'

    

    # Server continuous sync loop
    while (True):
        time.sleep(5)
        print 'Sending client updates...',
        client_after = [f for f in listdir(dir_name) if f[0]!='.']
        send_all(s, client_after)
        print 'done.'

        length = recv_all(s, SIZE_BUFF)
        client_additions = pickle.loads(recv_all(s, int(length)))
        if client_additions:
            print 'Sending files to server...',
            for f in client_additions:
                send_all(s, formatFile(f))
            print 'done.'

        length = recv_all(s, SIZE_BUFF)
        server_additions = pickle.loads(recv_all(s, int(length)))

        if server_additions:
            print 'Receiving files from server...',
            for f in server_additions:
                length = recv_all(s, SIZE_BUFF)
                recv_file = pickle.loads(recv_all(s, int(length)))
                with open('{}/{}'.format(dir_name, recv_file['name']), 'w') as f:
                    f.write(recv_file['content'])
            print 'done.'

        print 'Sending updated client list...',
        client_before = [f for f in listdir(dir_name) if f[0]!='.']
        send_all(s, client_before)
        print 'done.'
    
    s.close()
    print 'Connection closed.'

def recv_all(sock, length):
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            #raise EOFError('Socket closed {} bytes into a {}-byte message'.format(len(data), length))
            break
        data += more
    return data

def send_all(sock, data):
    formatted = pickle.dumps(data)
    sock.sendall(str(len(formatted)).zfill(SIZE_BUFF))
    sock.sendall(formatted)
    

def formatFile(file_name):
    with open('{}\{}'.format(dir_name, file_name), 'r') as f:
        file_content = f.read()
    
    file_data = {
        'name': file_name,
        'content': file_content
    }
    
    return file_data

if __name__ == '__main__':
    main(sys.argv)
