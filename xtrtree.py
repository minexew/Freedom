#!/usr/bin/env python3

import operator, sys, xtr

data = xtr.parse(sys.argv[1])

# begin, end, name, children
root = (0, None, '$', [])

def is_strict_subrange(a1, a2, b1, b2):
    return (a1 >= b1 and a2 < b2) or (a1 > b1 and a2 <= b2)

def intersects(a1, a2, b1, b2):
    return (a1 >= b1 and a2 <= b2) or (b1 >= a1 and b2 <= a2)

def stringify(node):
    length = node[1] - node[0] if node[1] is not None else 0
    return '%s (%s..%s\tlength = %d / 0x%X)' % (node[2], node[0], node[1], length, length)

def merge(node, other):
    return (node[0], node[1], node[2] + ' aka ' + other[2], node[3] + other[3])

def print_tree(node, indent=0):
    print('  ' * indent, end='')
    print(stringify(node))

    if len(node) < 4: return

    for i, child in enumerate(node[3]):
        print_tree(child, indent + 1)

        if i + 1 < len(node[3]):
            this_end = child[1]
            next_start = node[3][i + 1][0]
            if this_end < next_start:
                print_tree((this_end, next_start, '?'), indent + 1)

def put_into_tree(node, parent):
    #print(parent)

    i = 0
    while i < len(parent[3]):
        # FIXME: returning early aborts bad intersection checking
        child = parent[3][i]
        n1 = node[0]
        n2 = node[1]
        c1 = child[0]
        c2 = child[1]

        if is_strict_subrange(n1, n2, c1, c2):
            # node goes into child
            return put_into_tree(node, child)
        elif is_strict_subrange(c1, c2, n1, n2):
            # child goes into node, node takes child's place in tree
            # TODO: should check if node intersects with any sibling
            put_into_tree(child, node)

            del parent[3][i]
            i -= 1
        elif n1 == c1 and n2 == c2:
            #print('Warning: equal ranges for %s, %s - merging' % (stringify(node), stringify(child)))
            parent[3][i] = merge(child, node)
            return
        elif intersects(n1, n2, c1, c2):
            raise Exception('Intersection between %s, %s' % (stringify(node), stringify(child)))

        i += 1

    parent[3].append(node)

def sort_tree(node):
    for child in node[3]:
        sort_tree(child)

    node[3].sort(key=operator.itemgetter(0))

for entry in data:
    node = (entry[0], entry[1], entry[2], [])
    put_into_tree(node, root)

sort_tree(root)
print_tree(root)
