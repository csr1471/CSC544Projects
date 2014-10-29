from os import stat, listdir, remove
from shutil import copyfile

if __name__ == '__main__':
    dir1 = 'NetworkSync'
    dir2 = 'LocalSync'
    while(True):
        dir1_items = [x for x in listdir(dir1) if x[0]!='.']
        dir2_items = [x for x in listdir(dir2) if x[0]!='.']

        for filename in dir1_items:
            if filename not in dir2_items:
                copyfile('{}\{}'.format(dir1, filename), '{}\{}'.format(dir2, filename))
