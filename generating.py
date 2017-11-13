from os import listdir
from os.path import isfile, join

onlyfiles = [ f for f in listdir('./_posts') if isfile(join('./_posts/',f)) ]
categories = set()
for f in onlyfiles:
    reader = open(join('./_posts/',f))
    content = reader.readlines()
    for line in content:
        if line[:10] == 'categories':
            categories.add(line[12:].rstrip())
            break
print(categories)

output = open('./_data/catagories.yml', '+w')
for cate in categories:
    output.write('- name: ' + cate + '\n\n')
