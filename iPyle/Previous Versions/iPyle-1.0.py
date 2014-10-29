import socket, sys, re, Tkinter, tkFileDialog
import cPickle as pickle

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = sys.argv.pop() if len(sys.argv) == 3 else '127.0.0.1'
PORT = 1060

def selectDirectory():
    current_directory = Tkinter.Tk()
    directory_name = tkFileDialog.askdirectory(initialdir=current_directory, title='Select Folder...')
    current_directory.withdraw()
    
    return directory_name

def selectFile():
    current_directory = Tkinter.Tk()
    input_file = tkFileDialog.askopenfile(mode='r', initialdir=current_directory, title='Select File...')
    current_directory.withdraw()
    match = re.search('(.+)/(.+)', input_file.name)
    if match:
        file_path = match.group(1)
        file_name = match.group(2)
    file_content = input_file.read()
    input_file.close()

    return file_name, file_content      

# Server Code
if sys.argv[1:] == ['server']:
    directory = selectDirectory()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    sc, sockname = s.accept()
    sc.shutdown(socket.SHUT_WR)
    message = pickle.loads(sc.recv(2097152)) # Send up to 2 MB
    sc.close()
    s.close()
    print 'File received.'
    with open('{}/{}'.format(directory, message['filename']), 'w') as f:
        f.write(message['content'])

# Client Code
elif sys.argv[1:] == ['client']:
    #directory = selectDirectory()
    s.connect((HOST, PORT))
    file_name, file_content = selectFile()
    file_data = {
        'filename': file_name,
        'content': file_content
    }
    s.sendall(pickle.dumps(file_data))
    print 'File sent.'
    s.close()

# Usage Hint
else:
    print >> sys.stderr, 'usage: tcp_local.py server|client [host]'
