import socket, sys, time
from os import stat, listdir, remove, path
from shutil import copyfile

dir1 = 'NetworkSync'
dir2 = 'LocalSync'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = '127.0.0.1'
PORT = 12345

def main(args):
    if args[1:] == ['server']:
        s.bind((HOST, PORT))
        s.listen(1)
        print 'Listening at', s.getsockname()
        sc, sockname = s.accept()
        print 'We have accepted a connection from', sockname
        print 'Socket connects', sc.getsockname(), 'and', sc.getpeername()
        message = recv_all(sc, 16)
        print 'The incoming sixteen-octet message says', repr(message)
        sc.sendall('Farewell, client')
        print 'Reply sent, socket closed'
        sc.close()
    elif args[1:] == ['client']:
        s.connect((HOST, PORT))
        print 'Client has been assigned socket name', s.getsockname()
        s.sendall('Hi there, server')
        reply = recv_all(s, 16)
        print 'The server said', repr(reply)
        s.close()
    else:
        print >> sys.stderr, 'usage: iPile.py server|client'

def recv_all(sock, length):
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('socket closed {} bytes into a {}-byte message'.format(len(data), length))
        data += more
    return data

def iPyle():            
    initial_sync()
    before1, before2 = list_directories()
    
    while(True):
        time.sleep(2)
        after1, after2 = list_directories()

        # Sync file additions
        added1 = [f for f in after1 if not f in before1]
        added2 = [f for f in after2 if not f in before2]
        if added1:
            sync_add(added1, dir1, dir2)
        if added2:
            sync_add(added2, dir2, dir1)

        # Sync file removals
        removed1 = [f for f in before1 if not f in after1]
        removed2 = [f for f in before2 if not f in after2]
        if removed1:
            for filename in removed1:
                fullpath = '\\'.join([dir2, filename])
                remove(fullpath)
            print 'Removed:',','.join(removed1)
        if removed2:
            for filename in removed2:
                fullpath = '\\'.join([dir1, filename])
                remove(fullpath)
            print 'Removed: ',','.join(removed2)

        before1, before2 = list_directories()


def initial_sync():
    before1 = [f for f in listdir(dir1) if f[0]!='.']
    before2 = [f for f in listdir(dir2) if f[0]!='.']
    sync1 = [f for f in before1 if not f in before2]
    sync2 = [f for f in before2 if not f in before1]
    if sync1:
        sync_add(sync1, dir1, dir2)
    if sync2:
        sync_add(sync2, dir2, dir1)

def sync_add(filelist, source, dest):
    for filename in filelist:
        sourcepath = '\\'.join([source, filename])
        destpath = '\\'.join([dest, filename])
        if path.isdir(sourcepath):
            print '{} is a directory'.format(filename)
        else:
            copyfile(sourcepath, destpath)
    print 'Added: ',','.join(filelist)

def list_directories():
    return [f for f in listdir(dir1) if f[0]!='.'], [f for f in listdir(dir2) if f[0]!='.']

if __name__ == '__main__':
    main(sys.argv)
