#!/usr/bin/env python3

'''
PRM format description:

Header
======

(0-15)
u32     unk1
u32     entry_offset_list
u32     offset2
u32     num_entries

Entry Offset List
=================

repeat(num_entries) {
    u32 entry_offset
}

Entry
=====

size: 68 bytes

'''

import argparse, itertools, os, struct, sys
import fftools, xtr
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('prmfile')
parser.add_argument('--dumpall', dest='dump_into', metavar='output_dir')
parser.add_argument('--dump', dest='dump_entry', metavar='name')
parser.add_argument('-v', dest='verbose', action='store_true')
args = parser.parse_args()

f = open(args.prmfile, 'rb')
xtr.track(f, args.prmfile)

dump_dir = os.path.splitext(args.prmfile)[0] + '_prm'
os.makedirs(dump_dir, exist_ok=True)

def save_image(name, w, h, data):
    img = Image.new('RGBA', (w, h))
    pixels = img.load()

    for y in range(h):
        for x in range(w):
            pixels[x, y] = (data[((y * w) + x) * 4],
                                    data[((y * w) + x) * 4 + 1],
                                    data[((y * w) + x) * 4 + 2],
                                    data[((y * w) + x) * 4 + 3])

    img.save(name + '.png')

prm_header = struct.unpack('IIII', f.read(16))
print('PRM header: unk1=%d entry_offset_list=%d offset2=%d num_entries=%d' % prm_header)
entry_offset_list = prm_header[1]
num_entries = prm_header[3]

all_dump = open(os.path.join(dump_dir, '00multi.obj'), 'wt')
indices_skip = 0

'''def dump_0_to_438():
    dump_vertices(8)
    dump_indices()
    dump_wtf()
'''
def dump_vertices(count, print_, dump):
    if print_:
        print('%d vertices:' % count)

    for i in range(0, count):
        entry = struct.unpack('ffffffIII', f.read(36))

        if print_:
            print('\t(%g\t%g\t%g)\t(%g\t%g\t%g)\t#%08x\tunk1=%08X unk2=%08X' % entry)

        if dump:
            print('v %g %g %g' % (entry[0], entry[1], entry[2]), file=dump)

    #print(f.tell())

def triangulate(vertices):
    return [(vertices[i - 2], vertices[i - 1], vertices[i]) if i % 2 == 0 else
            (vertices[i - 1], vertices[i - 2], vertices[i]) for i in range(2, len(vertices))]

def dump_indices(print_, dump):
    primitives = struct.unpack('H', f.read(2))[0]

    if print_:
        print('%d primitives:' % primitives)

    for i in range(0, primitives):
        count = struct.unpack('H', f.read(2))[0]

        if print_:
            print('\t(%d : %d)' % (i, count), end='\t')

        indices = [indices_skip + struct.unpack('H', f.read(2))[0] for i in range(count)]

        if print_:
            print(' '.join([str(i) for i in indices]))

        if dump:
            if len(indices) == 2:
                print('l %s' % ' '.join([str(i + 1) for i in indices]), file=dump)
            else:
                for indices in triangulate(indices):
                    print('f %s' % ' '.join([str(i + 1) for i in indices]), file=dump)

    #print(f.tell())

def dump_matrix():
    print('\t\tunk=%08X' % struct.unpack('I', f.read(4))[0])

    for i in range(0, 2):
        entry = struct.unpack('fffI', f.read(16))

        print('\t\t(%g\t%g\t%g)\t#%08x' % entry)

    for i in range(0, 2):
        entry = struct.unpack('fff', f.read(12))

        print('\t\t(%g\t%g\t%g)' % entry)

    #print(f.tell())

def dump_entry(index, indent, dump=None):
    global indices_skip

    name = '%d.%d' % (index, indent)
    xtr.begin(f, '%s' % name)
    offset = f.tell()
    verbose = False

    print('    ' * indent, end='')
    print('entry %s (at %d / 0x%08X):' % (name, offset, offset))
    indent += 1

    if dump is None:
        dump = open(os.path.join(dump_dir, '%s.obj' % offset), 'wt')
        indices_skip = 0

        #dump = None
        #dump = all_dump if index == 137 else None

    if dump: print('o %s' % name, file=dump)

    entry_header = struct.unpack('IIIHHIIII', f.read(32))
    entry_header2 = struct.unpack('IIIIIIII', f.read(32))
    entry_header3 = struct.unpack('I', f.read(4))

    child_offset = entry_header[2]
    num_vertices = entry_header[4]
    bounds_offset = entry_header[5]
    vertices_offset = entry_header[6]
    indices_offset = entry_header2[7]

    print('    ' * indent, end='')
    print('flags=%08X unk=%d child_offset=%d unk=%d num_vertices=%d bounds_offset=%d vertices_offset=%d zero=%d zero=%d' % entry_header)
    print('    ' * indent, end='')
    print('zero=%d %d %d %d unk=%08X zero=%d unk=%08X indices_offset=%d' % entry_header2)
    print('    ' * indent, end='')
    print('count?=%d' % entry_header3)
    print('    ' * indent, end='')
    print('unk=%d %d %d %d (%g %g) %d %d (%g %g %g %g) %d %08X' % struct.unpack('IIIIffIIffffII', f.read(56)))
    print('    ' * indent, end='')
    print('(entry ends at %d)' % f.tell())

    xtr.end()

    f.seek(vertices_offset)
    xtr.begin(f, '%s_vertices' % name)
    dump_vertices(num_vertices, verbose, dump)
    xtr.end()

    f.seek(indices_offset)
    xtr.begin(f, '%s_indices' % name)
    dump_indices(verbose, dump)
    xtr.end()

    f.seek(bounds_offset)
    xtr.begin(f, '%s_bounds' % name)
    print('    ' * indent, end='')
    print('matrix:')
    dump_matrix()
    xtr.end()

    if dump:
        indices_skip += num_vertices

    if child_offset:
        print()
        f.seek(child_offset)
        #dump_4()
        dump_entry(index, indent, dump)

    indent -= 1
    print()

f.seek(entry_offset_list)

entries = []

for i in range(num_entries):
    offset = struct.unpack('I', f.read(4))[0]
    entries += [offset]
    #print('\t%d' % offset)

#num_to_dump = 9999
num_to_dump = len(entries)

print()

for index, offset in enumerate(entries[0:num_to_dump]):
    f.seek(offset & 0x01FFFFFF)
    dump_entry(index, 0)
