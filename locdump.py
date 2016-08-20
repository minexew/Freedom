#!/usr/bin/env python3

import argparse, itertools, os, struct, sys
import utils

parser = argparse.ArgumentParser()
parser.add_argument('locfile')
parser.add_argument('-v', dest='verbose', action='store_true')
args = parser.parse_args()

def dump_chunk(f, size, depth):
    offset = f.tell()
    ends_at = offset + size

    if depth > 0:
        name = utils.read_sz(f)

        print(' ' * depth, end='')
        print(name, end='\t')

        if f.tell() == ends_at:         # leaf node
            print()
            return
    else:
        name = None

    num_children = struct.unpack('B', f.read(1))[0]

    print('(%d entries' % num_children, end='')

    child_offsets = [0]

    for i in range(1, num_children):
        child_offset = struct.unpack('I', f.read(4))[0]
        child_offsets += [child_offset]

    print(', %d bytes - offsets ' % (ends_at - f.tell()) + ' '.join([str(i) for i in child_offsets]) + ')')

    child_offsets += [ends_at - f.tell()]

    for i in range(num_children):
        dump_chunk(f, child_offsets[i + 1] - child_offsets[i], depth + 1)

    if depth > 0 and num_children > 1:
        print(' ' * depth, end='')
        print('(end of %s)' % name)

f = open(args.locfile, 'rb')

f.seek(0, os.SEEK_END)
size = f.tell()
f.seek(0, os.SEEK_SET)

dump_chunk(f, size, 0)
