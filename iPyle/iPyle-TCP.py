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
    s.listen(1)
    sc, sa = s.accept()

    
    # Initial Sync
    print 'Initializing folder synchronization...',
    server_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    length = recv_all(sc, SIZE_BUFF)
    client_dirs = pickle.loads(recv_all(sc, int(length)))

    to_add_server_dirs = [f for f in client_dirs if not f in server_dirs]
    to_add_client_dirs = [f for f in server_dirs if not f in client_dirs]

    if to_add_server_dirs:
        for d in to_add_server_dirs:
            mkdir(d)

    send_all(sc, to_add_client_dirs)
    
    
    server_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
    length = recv_all(sc, SIZE_BUFF)
    client_files = pickle.loads(recv_all(sc, int(length)))

    to_add_server_files = [f for f in client_files if not f in server_files]
    to_add_client_files = [f for f in server_files if not f in client_files]
    
    send_all(sc, to_add_server_files)

    if to_add_server_files:
        for f in to_add_server_files:
            length = recv_all(sc, SIZE_BUFF)
            recv_file = pickle.loads(recv_all(sc, int(length)))
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])

    send_all(sc, to_add_client_files)
    
    if to_add_client_files:
        for f in to_add_client_files:
            send_all(sc, formatFile(f))
    print 'complete!'

    

    # Server continuous sync loop
    server_before_dirs = client_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    server_before_files = client_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]

    try:
        while (True):
            time.sleep(5)
            # Determine differentiation
            server_after_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]         
            length = recv_all(sc, SIZE_BUFF)
            client_after_dirs = pickle.loads(recv_all(sc, int(length)))

            server_after_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]     
            length = recv_all(sc, SIZE_BUFF)
            client_after_files = pickle.loads(recv_all(sc, int(length)))
            
            # Process Additions
            server_additions_dirs = [f for f in server_after_dirs if not f in server_before_dirs]
            client_additions_dirs = [f for f in client_after_dirs if not f in client_before_dirs]

            if client_additions_dirs:
                for d in client_additions_dirs:
                    mkdir(d)

            send_all(sc, server_additions_dirs)
            
            
            server_additions_files = [f for f in server_after_files if not f in server_before_files]
            client_additions_files = [f for f in client_after_files if not f in client_before_files]

            send_all(sc, client_additions_files)

            if client_additions_files:
                for f in client_additions_files:
                    length = recv_all(sc, SIZE_BUFF)
                    recv_file = pickle.loads(recv_all(sc, int(length)))
                    with open(recv_file['name'], 'w') as f:
                        f.write(recv_file['content'])

            send_all(sc, server_additions_files)
            
            if server_additions_files:
                for f in server_additions_files:
                    send_all(sc, formatFile(f))


            # Process Removals
            server_removals_files = [f for f in server_before_files if not f in server_after_files]
            client_removals_files = [f for f in client_before_files if not f in client_after_files]

            if client_removals_files:
                for f in client_removals_files:
                    remove(f)

            send_all(sc, server_removals_files)

            server_removals_dirs = [f for f in server_before_dirs if not f in server_after_dirs]
            client_removals_dirs = [f for f in client_before_dirs if not f in client_after_dirs]

            if client_removals_dirs:
                for d in client_removals_dirs:
                    rmdir(d)

            send_all(sc, server_removals_dirs)

            server_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            server_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]

            length = recv_all(sc, SIZE_BUFF)
            client_before_dirs = pickle.loads(recv_all(sc, int(length)))
            length = recv_all(sc, SIZE_BUFF)
            client_before_files = pickle.loads(recv_all(sc, int(length)))
    except (KeyboardInterrupt, ValueError, socket.error):
        pass

    sc.close()
    print 'Connection closed.'

def iPyleClient(HOST):
    s.connect((HOST, PORT))

    # Initial Sync
    print 'Initializing folder synchronization...',
    client_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    send_all(s, client_dirs)

    length = recv_all(s, SIZE_BUFF)
    to_add_client_dirs = pickle.loads(recv_all(s, int(length)))

    if to_add_client_dirs:
        for d in to_add_client_dirs:
            mkdir(d)


    client_files = ['{}/{}'.format(dir_path, f) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
    send_all(s, client_files)
    
    length = recv_all(s, SIZE_BUFF)
    to_add_server_files = pickle.loads(recv_all(s, int(length)))

    if to_add_server_files:
        for f in to_add_server_files:
            send_all(s, formatFile(f))

    
    length = recv_all(s, SIZE_BUFF)
    to_add_client_files = pickle.loads(recv_all(s, int(length)))
    if to_add_client_files:
        for f in to_add_client_files:
            length = recv_all(s, SIZE_BUFF)
            recv_file = pickle.loads(recv_all(s, int(length)))
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])
    print 'Initial sync complete!'

    

    # Server continuous sync loop
    try:
        while (True):
            time.sleep(5)

            # Process Additions
            client_after_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            send_all(s, client_after_dirs)
            
            client_after_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
            send_all(s, client_after_files)

            length = recv_all(s, SIZE_BUFF)
            server_additions_dirs = pickle.loads(recv_all(s, int(length)))
            if server_additions_dirs:
                for d in server_additions_dirs:
                    mkdir(d)
            

            length = recv_all(s, SIZE_BUFF)
            client_additions_files = pickle.loads(recv_all(s, int(length)))
            if client_additions_files:
                for f in client_additions_files:
                    send_all(s, formatFile(f))

            length = recv_all(s, SIZE_BUFF)
            server_additions_files = pickle.loads(recv_all(s, int(length)))

            if server_additions_files:
                for f in server_additions_files:
                    length = recv_all(s, SIZE_BUFF)
                    recv_file = pickle.loads(recv_all(s, int(length)))
                    with open(recv_file['name'], 'w') as f:
                        f.write(recv_file['content'])

            # Process Removals
            length = recv_all(s, SIZE_BUFF)            
            server_removals_files = pickle.loads(recv_all(s, int(length)))

            if server_removals_files:
                for f in server_removals_files:
                    remove(f)

            length = recv_all(s, SIZE_BUFF)
            server_removals_dirs = pickle.loads(recv_all(s, int(length)))

            if server_removals_dirs:
                for d in server_removals_dirs:
                    rmdir(d)

            client_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            client_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
            send_all(s, client_before_dirs)
            send_all(s, client_before_files)
    except (KeyboardInterrupt, ValueError, socket.error):
        pass
        
    
    s.close()
    print 'Connection closed.'
    

def recv_all(sock, length):
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
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
