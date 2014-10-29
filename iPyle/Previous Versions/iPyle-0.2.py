import time
from os import stat, listdir, remove
from shutil import copyfile

# Folders should be mirrors
def main():
    dir1 = 'NetworkSync'
    dir2 = 'LocalSync'

    before1 = dict([(f, None) for f in listdir(dir1)])
    before2 = dict([(f, None) for f in listdir(dir2)])
    
    while(True):
        time.sleep(5)
        after1 = dict([(f, None) for f in listdir(dir1)])
        after2 = dict([(f, None) for f in listdir(dir2)])

        added1 = [f for f in after1 if not f in before1]
        added2 = [f for f in after2 if not f in before2]
        
        removed1 = [f for f in before1 if not f in after1]
        removed2 = [f for f in before2 if not f in after2]

        if added1:
            print "Added to 1: ",",".join(added1)
        if removed1:
            print "Removed to 1: ",",".join(removed1)
        if added2:
            print "Added to 2: ",",".join(added2)
        if removed2:
            print "Removed from 2: ",",".join(removed2)

        addto1 = [f for f in after2 if not f in before1]
        addto2 = [f for f in after1 if not f in before2]
        if addto1:
            for filename in addto1:
                fullpath1 = '\\'.join([dir1, filename])
                fullpath2 = '\\'.join([dir2, filename])
                copyfile(fullpath2, fullpath1)
        if addto2:
            for filename in addto2:
                fullpath1 = '\\'.join([dir1, filename])
                fullpath2 = '\\'.join([dir2, filename])
                copyfile(fullpath1, fullpath2)            

        removefrom1 = [f for f in after2 if f in after1]
        removefrom2 = [f for f in after1 if f in after2]
        if removefrom1:
            for filename in removefrom1:
                fullpath1 = '\\'.join([dir1, filename])
                remove(fullpath1)
        if removefrom2:
            for filename in removefrom2:
                fullpath2 = '\\'.join([dir2, filename])
                remove(fullpath2)

        
        before1 = dict([(f, None) for f in listdir(dir1)])
        before2 = dict([(f, None) for f in listdir(dir2)])

##        dir2_items = [x for x in listdir(dir2) if x[0]!='.']
##
##        for filename in dir1_items:
##            if filename not in dir2_items:
##                fullpath1 = '\\'.join([dir1, filename])
##                fullpath2 = '\\'.join([dir2, filename])
##                copyfile(fullpath1, fullpath2)
##                print '{} has been added to {}'.format(filename, dir2)
##        for filename in dir2_items:
##            if filename not in dir1_items:
##                fullpath2 = '\\'.join([dir2, filename])
##                remove(fullpath2)
##                print '{} has been removed from {}'.format(filename, dir2)


if __name__ == '__main__':
    main()

