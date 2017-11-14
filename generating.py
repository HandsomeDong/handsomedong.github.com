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

for cate in categories:
    output = open('./_post_categories/'+cate+'.markdown', 'w')
    output.write('--- \n')
    output.write('name: ' + cate + '\n')
    output.write('--- \n')
