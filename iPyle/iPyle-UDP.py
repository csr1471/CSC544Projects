import socket, sys, time
import cPickle as pickle
from os import listdir, remove, path, walk, mkdir, rmdir

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
PORT = 12345
MAX = 65535

sync_dir = 'NetworkSync'

def main(args):
    HOST = args.pop() if len(args) == 3 else '127.0.0.1'
    if args[1:] == ['server']:
        iPyleServer(HOST)
    elif args[1:] == ['client']:
        iPyleClient(HOST)
    else:
        print 'Usage: python iPyle-UDP.py server|client [hostname]'

def iPyleServer(HOST):
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))

    # Initial Sync
    print 'Initializing folder synchronization...',
    server_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    client_dirs, client_addr = s.recvfrom(MAX)
    s.sendto('1', client_addr)
    client_dirs = pickle.loads(client_dirs)

    to_add_server_dirs = [f for f in client_dirs if not f in server_dirs]
    to_add_client_dirs = [f for f in server_dirs if not f in client_dirs]

    if to_add_server_dirs:
        for d in to_add_server_dirs:
            mkdir(d)

    send_to(s, pickle.dumps(to_add_client_dirs), client_addr)
    
    server_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
    client_files, client_addr = s.recvfrom(MAX)
    client_files = pickle.loads(client_files)

    to_add_server_files = [f for f in client_files if not f in server_files]
    to_add_client_files = [f for f in server_files if not f in client_files]
    
    send_to(s, pickle.dumps(to_add_server_files), client_addr)

    if to_add_server_files:
        for f in to_add_server_files:
            recv_file, client_addr = s.recvfrom(MAX)
            s.sendto('1', client_addr)
            recv_file = pickle.loads(recv_file)
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])

    send_to(s, pickle.dumps(to_add_client_files), client_addr)
    
    if to_add_client_files:
        for f in to_add_client_files:
            send_to(s, pickle.dumps(formatFile(f)), client_addr)
    print 'complete!'

    

    # Server continuous sync loop
    server_before_dirs = client_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    server_before_files = client_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]

    try:
        while (True):
            time.sleep(5)
            # Determine differentiation
            server_after_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]         
            client_after_dirs, client_addr = s.recvfrom(MAX)
            s.sendto('1', client_addr)
            client_after_dirs = pickle.loads(client_after_dirs)

            server_after_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]     
            client_after_files, client_addr = s.recvfrom(MAX)
            s.sendto('1', client_addr)
            client_after_files = pickle.loads(client_after_files)
            
            # Process Additions
            server_additions_dirs = [f for f in server_after_dirs if not f in server_before_dirs]
            client_additions_dirs = [f for f in client_after_dirs if not f in client_before_dirs]

            if client_additions_dirs:
                for d in client_additions_dirs:
                    mkdir(d)

            send_to(s, pickle.dumps(server_additions_dirs), client_addr)
            
            
            server_additions_files = [f for f in server_after_files if not f in server_before_files]
            client_additions_files = [f for f in client_after_files if not f in client_before_files]

            send_to(s, pickle.dumps(client_additions_files), client_addr)

            if client_additions_files:
                for f in client_additions_files:
                    recv_file, client_addr = s.recvfrom(MAX)
                    s.sendto('1', client_addr)
                    recv_file = pickle.loads(recv_file)
                    with open(recv_file['name'], 'w') as f:
                        f.write(recv_file['content'])

            send_to(s, pickle.dumps(server_additions_files), client_addr)
            
            if server_additions_files:
                for f in server_additions_files:
                    send_to(s, pickle.dumps(formatFile(f)), client_addr)


            # Process Removals
            server_removals_files = [f for f in server_before_files if not f in server_after_files]
            client_removals_files = [f for f in client_before_files if not f in client_after_files]

            if client_removals_files:
                for f in client_removals_files:
                    remove(f)

            send_to(s, pickle.dumps(server_removals_files), client_addr)

            server_removals_dirs = [f for f in server_before_dirs if not f in server_after_dirs]
            client_removals_dirs = [f for f in client_before_dirs if not f in client_after_dirs]

            if client_removals_dirs:
                for d in client_removals_dirs:
                    rmdir(d)

            send_to(s, pickle.dumps(server_removals_dirs), client_addr)

            server_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            server_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]

            client_before_dirs, client_addr = s.recvfrom(MAX)
            s.sendto('1', client_addr)
            client_before_dirs = pickle.loads(client_before_dirs)
            client_before_files, client_addr = s.recvfrom(MAX)
            s.sendto('1', client_addr)
            client_before_files = pickle.loads(client_before_files)

    except (KeyboardInterrupt, ValueError, socket.error):
        pass

    s.close()
    print 'Connection closed.'

def iPyleClient(HOST):
    server_addr = (HOST, PORT)

    # Initial Sync
    print 'Initializing folder synchronization...',
    client_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    send_to(s, pickle.dumps(client_dirs), server_addr)

    to_add_client_dirs, server_addr = s.recvfrom(MAX)
    s.sendto('1', server_addr)
    to_add_client_dirs = pickle.loads(to_add_client_dirs)

    if to_add_client_dirs:
        for d in to_add_client_dirs:
            mkdir(d)


    client_files = ['{}/{}'.format(dir_path, f) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
    send_to(s, pickle.dumps(client_files), server_addr)
    
    to_add_server_files, server_addr = s.recvfrom(MAX)
    s.sendto('1', server_addr)
    to_add_server_files = pickle.loads(to_add_server_files)

    if to_add_server_files:
        for f in to_add_server_files:
            send_to(s, pickle.dumps(formatFile(f)), server_addr)

    
    to_add_client_files, server_addr = s.recvfrom(MAX)
    s.sendto('1', server_addr)
    to_add_client_files = pickle.loads(to_add_client_files)
    if to_add_client_files:
        for f in to_add_client_files:
            recv_file, server_addr = s.recvfrom(MAX)
            s.sendto('1', server_addr)
            recv_file = pickle.loads(recv_file)
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])
    print 'Initial sync complete!'

    

    # Server continuous sync loop
    try:
        while (True):
            time.sleep(5)

            # Process Additions
            client_after_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            send_to(s, pickle.dumps(client_after_dirs), server_addr)
            
            client_after_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
            send_to(s, pickle.dumps(client_after_files), server_addr)

            server_additions_dirs, server_addr = s.recvfrom(MAX)
            s.sendto('1', server_addr)
            server_additions_dirs = pickle.loads(server_additions_dirs)
            if server_additions_dirs:
                for d in server_additions_dirs:
                    mkdir(d)

            client_additions_files, server_addr = s.recvfrom(MAX)
            s.sendto('1', server_addr)
            client_additions_files = pickle.loads(client_additions_files)
            if client_additions_files:
                for f in client_additions_files:
                    send_to(s, pickle.dumps(formatFile(f)), server_addr)

            server_additions_files, server_addr = s.recvfrom(MAX)
            s.sendto('1', server_addr)
            server_additions_files = pickle.loads(server_additions_files)

            if server_additions_files:
                for f in server_additions_files:
                    recv_file, server_addr = s.recvfrom(MAX)
                    s.sendto('1', server_addr)
                    recv_file = pickle.loads(recv_file)
                    with open(recv_file['name'], 'w') as f:
                        f.write(recv_file['content'])

            # Process Removals
            server_removals_files, server_addr = s.recvfrom(MAX)
            s.sendto('1', server_addr)
            server_removals_files = pickle.loads(server_removals_files)

            if server_removals_files:
                for f in server_removals_files:
                    remove(f)

            server_removals_dirs, server_addr = s.recvfrom(MAX)
            s.sendto('1', server_addr)
            server_removals_dirs = pickle.loads(server_removals_dirs)

            if server_removals_dirs:
                for d in server_removals_dirs:
                    rmdir(d)

            client_before_dirs = ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
            client_before_files = ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
            send_to(s, pickle.dumps(client_before_dirs), server_addr)
            send_to(s, pickle.dumps(client_before_files), server_addr)
    except (KeyboardInterrupt, ValueError, socket.error):
        pass
        
    
    s.close()
    print 'Connection closed.'
    

def formatFile(file_name):
    with open(file_name, 'r') as f:
        file_content = f.read()
    
    file_data = {
        'name': file_name,
        'content': file_content
    }
    return file_data

def send_to(sock, data, addr):
    delay = 0.1
    while (True):
        sock.sendto(data, addr)
        sock.settimeout(delay)
        try:
            data, sender_addr = sock.recvfrom(1)
        except socket.timeout:
            delay *= 2
            if delay > 5.0:
                raise RuntimeError('Poor connection. Try again later.')
        except:
            raise
        else:
            break
if __name__ == '__main__':
    main(sys.argv)
