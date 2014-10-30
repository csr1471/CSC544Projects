import socket, sys, time
import cPickle as pickle
from os import listdir, remove, path, walk, mkdir, rmdir

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = 12345
SIZE_BUFF = 8

sync_dir = 'NetworkSync'

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
    print 'Listening...',
    s.listen(1)
    sc, sa = s.accept()
    print 'connected to {} on port {}'.format(sc.getpeername()[0], PORT)

    
    # Initial Sync
    print 'Receiving client directory list...',
    server_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    length = recv_all(sc, SIZE_BUFF)
    client_dirs = pickle.loads(recv_all(sc, int(length)))
    print 'done.'

    to_add_server_dirs = [f for f in client_dirs if not f in server_dirs]
    to_add_client_dirs = [f for f in server_dirs if not f in client_dirs]

    if to_add_server_dirs:
        print 'Creating folders on server...',
        for d in to_add_server_dirs:
            mkdir(d)
        print 'done.'

    send_all(sc, to_add_client_dirs)
    
    
    print 'Receiving client file list...',
    server_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
    length = recv_all(sc, SIZE_BUFF)
    client_files = pickle.loads(recv_all(sc, int(length)))
    print 'done.'

    to_add_server_files = [f for f in client_files if not f in server_files]
    to_add_client_files = [f for f in server_files if not f in client_files]
    
    send_all(sc, to_add_server_files)

    if to_add_server_files:
        print 'Receiving files from server...',
        for f in to_add_server_files:
            length = recv_all(sc, SIZE_BUFF)
            recv_file = pickle.loads(recv_all(sc, int(length)))
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])
        print 'done.'

    send_all(sc, to_add_client_files)
    
    if to_add_client_files:
        print 'Sending files to client...',
        for f in to_add_client_files:
            send_all(sc, formatFile(f))
        print 'done.'
    print 'Initial sync complete!'

    

    # Server continuous sync loop
    server_before_dirs = client_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    server_before_files = client_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]

    try:
        while (True):
            time.sleep(5)

            server_after_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            print 'Receiving client folder updates...',            
            length = recv_all(sc, SIZE_BUFF)
            client_after_dirs = pickle.loads(recv_all(sc, int(length)))
            print 'done.'

            server_after_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
            print 'Receiving client file updates...',            
            length = recv_all(sc, SIZE_BUFF)
            client_after_files = pickle.loads(recv_all(sc, int(length)))
            print 'done.'
            
            # Process Additions
            server_additions_dirs = [f for f in server_after_dirs if not f in server_before_dirs]
            client_additions_dirs = [f for f in client_after_dirs if not f in client_before_dirs]

            if client_additions_dirs:
                print 'Creating folders on server...',
                for d in client_additions_dirs:
                    mkdir(d)
                print 'done'

            send_all(sc, server_additions_dirs)
            
            
            server_additions_files = [f for f in server_after_files if not f in server_before_files]
            client_additions_files = [f for f in client_after_files if not f in client_before_files]

            send_all(sc, client_additions_files)

            if client_additions_files:
                print 'Receiving files from client...',
                for f in client_additions_files:
                    length = recv_all(sc, SIZE_BUFF)
                    recv_file = pickle.loads(recv_all(sc, int(length)))
                    with open(recv_file['name'], 'w') as f:
                        f.write(recv_file['content'])
                print 'done.'

            send_all(sc, server_additions_files)
            
            if server_additions_files:
                print 'Sending files to client...',
                for f in server_additions_files:
                    send_all(sc, formatFile(f))
                print 'done.'


            # Process Removals
            server_removals_files = [f for f in server_before_files if not f in server_after_files]
            client_removals_files = [f for f in client_before_files if not f in client_after_files]

            if client_removals_files:
                print 'Removing files from server...',
                for f in client_removals_files:
                    remove(f)
                print 'done.'

            send_all(sc, server_removals_files)

            server_removals_dirs = [f for f in server_before_dirs if not f in server_after_dirs]
            client_removals_dirs = [f for f in client_before_dirs if not f in client_after_dirs]

            if client_removals_dirs:
                print 'Removing folders from server...',
                for d in client_removals_dirs:
                    rmdir(d)
                print 'done.'

            send_all(sc, server_removals_dirs)

            print 'Refreshing folder lists...',
            server_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            server_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]

            length = recv_all(sc, SIZE_BUFF)
            client_before_dirs = pickle.loads(recv_all(sc, int(length)))
            length = recv_all(sc, SIZE_BUFF)
            client_before_files = pickle.loads(recv_all(sc, int(length)))
            print 'done.'
    except (KeyboardInterrupt, ValueError, socket.error):
        pass

    sc.close()
    print 'Connection closed.'

def iPyleClient(HOST):
    print 'Establishing a connection...',
    s.connect((HOST, PORT))
    print 'connected to {} on port {}'.format(HOST, s.getsockname()[1])


    # Initial Sync    
    print 'Sending client directory list...',
    client_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    send_all(s, client_dirs)
    print 'done.'

    length = recv_all(s, SIZE_BUFF)
    to_add_client_dirs = pickle.loads(recv_all(s, int(length)))

    if to_add_client_dirs:
        print 'Adding folders to client...',
        for d in to_add_client_dirs:
            mkdir(d)
        print 'done.'


    print 'Sending client file list...',
    client_files = ['{}/{}'.format(dir_path, f) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
    send_all(s, client_files)
    print 'done.'
    
    length = recv_all(s, SIZE_BUFF)
    to_add_server_files = pickle.loads(recv_all(s, int(length)))

    if to_add_server_files:
        print 'Sending files to server...',
        for f in to_add_server_files:
            send_all(s, formatFile(f))
        print 'done.'

    
    length = recv_all(s, SIZE_BUFF)
    to_add_client_files = pickle.loads(recv_all(s, int(length)))
    if to_add_client_files:
        print 'Receiving files from server...',
        for f in to_add_client_files:
            length = recv_all(s, SIZE_BUFF)
            recv_file = pickle.loads(recv_all(s, int(length)))
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])
        print 'done.'
    print 'Initial sync complete!'

    

    # Server continuous sync loop
    try:
        while (True):
            time.sleep(5)

            # Process Additions
            print 'Sending client folders updates...',
            client_after_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            send_all(s, client_after_dirs)
            print 'done.'
            
            print 'Sending client files updates...',
            client_after_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
            send_all(s, client_after_files)
            print 'done.'

            length = recv_all(s, SIZE_BUFF)
            server_additions_dirs = pickle.loads(recv_all(s, int(length)))
            if server_additions_dirs:
                print 'Creating directories on client...',
                for d in server_additions_dirs:
                    mkdir(d)
                print 'done.'
            

            length = recv_all(s, SIZE_BUFF)
            client_additions_files = pickle.loads(recv_all(s, int(length)))
            if client_additions_files:
                print 'Sending files to server...',
                for f in client_additions_files:
                    send_all(s, formatFile(f))
                print 'done.'

            length = recv_all(s, SIZE_BUFF)
            server_additions_files = pickle.loads(recv_all(s, int(length)))

            if server_additions_files:
                print 'Receiving files from server...',
                for f in server_additions_files:
                    length = recv_all(s, SIZE_BUFF)
                    recv_file = pickle.loads(recv_all(s, int(length)))
                    with open(recv_file['name'], 'w') as f:
                        f.write(recv_file['content'])
                print 'done.'

            # Process Removals
            length = recv_all(s, SIZE_BUFF)            
            server_removals_files = pickle.loads(recv_all(s, int(length)))

            if server_removals_files:
                print 'Removing files from client...',
                for f in server_removals_files:
                    remove(f)
                print 'done.'

            length = recv_all(s, SIZE_BUFF)
            server_removals_dirs = pickle.loads(recv_all(s, int(length)))

            if server_removals_dirs:
                print 'Removing folders from client...',
                for d in server_removals_dirs:
                    rmdir(d)
                print 'done.'

            print 'Sending updated client list...',
            client_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            client_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
            send_all(s, client_before_dirs)
            send_all(s, client_before_files)
            print 'done.'
    except (KeyboardInterrupt, ValueError, socket.error):
        pass
        
    
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
    with open(file_name, 'r') as f:
        file_content = f.read()
    
    file_data = {
        'name': file_name,
        'content': file_content
    }
    
    return file_data

if __name__ == '__main__':
    main(sys.argv)
