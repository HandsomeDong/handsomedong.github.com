from os import listdir
from os.path import isfile, join


def new_node():




onlyfiles = [ f for f in listdir('./_posts') if isfile(join('./_posts/',f)) ]
categories = set()
posts = []
for f in onlyfiles:
    reader = open(join('./_posts/',f))
    content = reader.readlines()
    post = {}
    for line in content:
        if line[:10] == 'categories':
            categories.add(line[12:].rstrip())
            post['categories'] = line[12:].rstrip()
        if line[:5] == 'title':
            post['title'] = line[7:].rstrip()
print(posts)

for cate in categories:
    output = open('./_post_categories/'+cate+'.markdown', 'w')
    output.write('--- \n')
    output.write('name: ' + cate + '\n')
    output.write('--- \n')
