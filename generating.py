from os import listdir
from os.path import isfile, join


def new_node(idd, label, value, r, g, b):
    node = ''' <node id="%s" label='%s'>
                  <attvalues>
                    <attvalue for="modularity_class" value="0"></attvalue>
                   </attvalues>
                   <viz:size value="%s"></viz:size>
                   <viz:color r="%s" g="%s" b="%s"></viz:color> 
                 </node>''' % (idd, label, value, r, g, b)
    return node


def new_edge(idd, source, target, weight):
    edge = '''
          <edge id="%s" source="%s" target="%s" weight="%s">
                   <attvalues></attvalues>
                 </edge>''' % (idd, source, target, weight)
    return edge


onlyfiles = [f for f in listdir('./_posts') if isfile(join('./_posts/',f)) ]
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
    posts.append(post)
print(posts)

front = open('./assets/data/front.gexf', 'r').read()
end = open('./assets/data/end.gexf', 'r').read()

graph_output = open('./assets/data/graph.gexf', 'w')
graph_output.write(front)
node_index = 0
cate_count = {}
name2index = {}
relation = []
for post in posts:
    if post['categories'] not in cate_count:
        cate_count[post['categories']] = 0
    cate_count[post['categories']] += 7
    graph_output.write(new_node(node_index, post['title'], '7', '0', '0', '0'))
    name2index[post['title']] = node_index
    relation.append((post['title'], post['categories']))
    node_index += 1


for cate in categories:
    output = open('./_post_categories/'+cate+'.markdown', 'w')
    output.write('--- \n')
    output.write('name: ' + cate + '\n')
    output.write('--- \n')
    graph_output.write(new_node(node_index, cate, str(cate_count[cate]), '100', '100', '100'))
    name2index[cate] = node_index
    relation.append((cate, 'root'))
    node_index += 1
graph_output.write(new_node(node_index, 'root', str(sum([cate_count[key] for key in cate_count])), '200', '200', '200'))
name2index['root'] = node_index

graph_output.write('''\n  </nodes>
                       <edges>\n''')

edge_index = 0
for rel in relation:
    graph_output.write(new_edge(edge_index, name2index[rel[0]], name2index[rel[1] ], 1))
    edge_index += 1

graph_output.write(end)
