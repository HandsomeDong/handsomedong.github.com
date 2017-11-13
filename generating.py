from os import listdir
from os.path import isfile, join

onlyfiles = [ f for f in listdir('./_posts') if isfile(join('./_posts/',f)) ]
print(onlyfiles)
for f in onlyfiles:
    reader = open(join('./_posts/',f))
    print(reader.readlines())
