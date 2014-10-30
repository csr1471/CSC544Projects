import socket, sys, time
import cPickle as pickle
from os import listdir, remove, path, walk, mkdir, rmdir
from random import randint

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
    server_dirs = list_dir()
    client_dirs, client_addr = recv_from(s, 0)

    client_dirs = pickle.loads(client_dirs)

    to_add_server_dirs = [f for f in client_dirs if not f in server_dirs]
    to_add_client_dirs = [f for f in server_dirs if not f in client_dirs]

    if to_add_server_dirs:
        for d in to_add_server_dirs:
            mkdir(d)

    send_to(s, pickle.dumps(to_add_client_dirs), client_addr)
    
    server_files = list_files()
    client_files, client_addr = recv_from(s, 0)
    client_files = pickle.loads(client_files)

    to_add_server_files = [f for f in client_files if not f in server_files]
    to_add_client_files = [f for f in server_files if not f in client_files]
    
    send_to(s, pickle.dumps(to_add_server_files), client_addr)

    if to_add_server_files:
        for f in to_add_server_files:
            recv_file, client_addr = recv_from(s, 0)
        
            recv_file = pickle.loads(recv_file)
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])

    send_to(s, pickle.dumps(to_add_client_files), client_addr)
    
    if to_add_client_files:
        for f in to_add_client_files:
            send_to(s, pickle.dumps(formatFile(f)), client_addr)
    print 'complete!'

    

    # Server continuous sync loop
    server_before_dirs = client_before_dirs = list_dir()
    server_before_files = client_before_files = list_files()

    try:
        while (True):
            time.sleep(5)
            print 'Refreshing folders...'
            # Determine differentiation
            server_after_dirs = list_dir()         
            client_after_dirs, client_addr = recv_from(s, 0)
        
            client_after_dirs = pickle.loads(client_after_dirs)

            server_after_files = list_files()     
            client_after_files, client_addr = recv_from(s, 0)
        
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
                    drop = randint(0, 1)
                    recv_file, client_addr = recv_from(s, drop)
                    if not drop: # Drop half of the file syncs
                        recv_file = pickle.loads(recv_file)
                        with open(recv_file['name'], 'w') as f:
                            f.write(recv_file['content'])
                    else:
                        print 'Unable to sync files from client.'

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

            server_before_dirs = list_dir()
            server_before_files = list_files()

            client_before_dirs, client_addr = recv_from(s, 0)
        
            client_before_dirs = pickle.loads(client_before_dirs)
            client_before_files, client_addr = recv_from(s, 0)
        
            client_before_files = pickle.loads(client_before_files)

    except (KeyboardInterrupt, ValueError, OSError, socket.error):
        pass

    s.close()
    print 'Connection closed.'

def iPyleClient(HOST):
    server_addr = (HOST, PORT)

    # Initial Sync
    print 'Initializing folder synchronization...',
    client_dirs = list_dir()
    send_to(s, pickle.dumps(client_dirs), server_addr)

    to_add_client_dirs, server_addr = recv_from(s, 0)
    
    to_add_client_dirs = pickle.loads(to_add_client_dirs)

    if to_add_client_dirs:
        for d in to_add_client_dirs:
            mkdir(d)


    client_files = list_files()
    send_to(s, pickle.dumps(client_files), server_addr)
    
    to_add_server_files, server_addr = recv_from(s, 0)
    
    to_add_server_files = pickle.loads(to_add_server_files)

    if to_add_server_files:
        for f in to_add_server_files:
            send_to(s, pickle.dumps(formatFile(f)), server_addr)

    
    to_add_client_files, server_addr = recv_from(s, 0)
    
    to_add_client_files = pickle.loads(to_add_client_files)
    if to_add_client_files:
        for f in to_add_client_files:
            recv_file, server_addr = recv_from(s, 0)
            
            recv_file = pickle.loads(recv_file)
            with open(recv_file['name'], 'w') as f:
                f.write(recv_file['content'])
    print 'Initial sync complete!'

    

    # Server continuous sync loop
    try:
        while (True):
            time.sleep(5)
            print 'Refreshing folders...'

            # Process Additions
            client_after_dirs = list_dir()
            send_to(s, pickle.dumps(client_after_dirs), server_addr)
            
            client_after_files = list_files()
            send_to(s, pickle.dumps(client_after_files), server_addr)

            server_additions_dirs, server_addr = recv_from(s, 0)
            
            server_additions_dirs = pickle.loads(server_additions_dirs)
            if server_additions_dirs:
                for d in server_additions_dirs:
                    mkdir(d)

            client_additions_files, server_addr = recv_from(s, 0)
            
            client_additions_files = pickle.loads(client_additions_files)
            if client_additions_files:
                for f in client_additions_files:
                    send_to(s, pickle.dumps(formatFile(f)), server_addr)

            server_additions_files, server_addr = recv_from(s, 0)
            
            server_additions_files = pickle.loads(server_additions_files)

            if server_additions_files:
                for f in server_additions_files:
                    drop = randint(0, 1)
                    recv_file, server_addr = recv_from(s, drop)
                    if not drop:
                        recv_file = pickle.loads(recv_file)
                        with open(recv_file['name'], 'w') as f:
                            f.write(recv_file['content'])
                    else:
                        print 'Unable to sync files from server.'

            # Process Removals
            server_removals_files, server_addr = recv_from(s, 0)
            
            server_removals_files = pickle.loads(server_removals_files)

            if server_removals_files:
                for f in server_removals_files:
                    remove(f)

            server_removals_dirs, server_addr = recv_from(s, 0)
            
            server_removals_dirs = pickle.loads(server_removals_dirs)

            if server_removals_dirs:
                for d in server_removals_dirs:
                    rmdir(d)

            client_before_dirs = list_dir()
            client_before_files = list_files()
            send_to(s, pickle.dumps(client_before_dirs), server_addr)
            send_to(s, pickle.dumps(client_before_files), server_addr)
    except (KeyboardInterrupt, ValueError, OSError, socket.error):
        pass
        
    
    s.close()
    print 'Connection closed.'
    

def list_dir():
    try:
        return ['{}/{}'.format(sync_dir, f) for f in [dir_name for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) if dir_name][0]]
    except IndexError:
        return []

def list_files():
    return ['/'.join('{}/{}'.format(dir_path, f).split('\\')) for dir_path, dir_name, file_name in walk(path.expanduser(sync_dir)) for f in file_name]
    
def formatFile(file_name):
    with open(file_name, 'r') as f:
        file_content = f.read()
    
    file_data = {
        'name': file_name,
        'content': file_content
    }
    return file_data


def send_to(conn, data, addr):
    delay = 0.1
    while (True):
        conn.sendto(data, addr)
        conn.settimeout(delay)
        try:
            data, addr = conn.recvfrom(MAX)
        except socket.timeout:
            delay *= 2
            if delay > 5.0:
                print 'I think the connection is lost.'
                conn.close()
        except error:
            print 'Network is unreachable'
            conn.close()
        except:
            conn.close()
            raise
        else:
            break

def recv_from(conn, drop):
    data, addr = conn.recvfrom(MAX)
    if not drop:
        conn.sendto('', addr)
        return data, addr
    else:
        conn.sendto('', addr)
        return pickle.dumps(''), addr
    
if __name__ == '__main__':
    main(sys.argv)
