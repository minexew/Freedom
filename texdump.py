#!/usr/bin/env python3

import argparse, itertools, os, struct, sys
import fftools
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('texfile')
parser.add_argument('--dumpall', dest='dump_into', metavar='output_dir')
parser.add_argument('--dump', dest='dump_entry', metavar='name')
parser.add_argument('-v', dest='verbose', action='store_true')
args = parser.parse_args()

f = open(args.texfile, 'rb')

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

header = struct.unpack('IIII', f.read(16))
print('TEX header: offset1=%d offset2=%d version=%d,%d' % header)

while True:
    offset = f.tell()

    if offset == header[0]:
        print('Content end at %d' % offset)
        break

    entry_header = struct.unpack('I4s4sI', f.read(16))
    entry_header2 = struct.unpack('HHIIII', f.read(20))

    entry_size = entry_header[0]
    fmt1 = entry_header[1]
    fmt2 = entry_header[2]
    id_ = entry_header[3]
    h = entry_header2[0]
    w = entry_header2[1]
    num_images = entry_header2[2]
    flags = entry_header2[3]

    if args.verbose:
        print('@(%d)' % (offset), end='\t')
        print('TEX entry: entry_size=%d fmt1=%s fmt2=%s id=%d' % entry_header)
        print('\th=%d w=%d num_images=%d flags=%08X zero1=%d unk1=%08X' % entry_header2)

    name = fftools.read_sz(f)

    if args.verbose:
        print('\tname=%s' % name)

    for i in range(num_images):
        image_size = struct.unpack('I', f.read(4))[0]

        if args.verbose:
            print('\t(%d)\timage_size=%d' % (i, image_size))

        if i == 0:
            if (args.dump_entry and name == args.dump_entry) or args.dump_into:
                if fmt1 != b'ABGR':
                    print('skipping dump of "%s": unknown format %s' % (name, fmt1))
                else:
                    image_data = f.read(image_size)
                    f.seek(-len(image_data), 1)

                    if args.dump_entry and name == args.dump_entry:
                        save_image(name, w, h, image_data)

                    if args.dump_into:
                        save_image(os.path.join(args.dump_into, name), w, h, image_data)

        f.seek(image_size, 1)

    if fmt1 == b'NLAP':
        palette_entries = struct.unpack('I', f.read(4))[0]

        if args.verbose:
            print('\t%d palette entries' % palette_entries)

        for j in range(palette_entries):
            color = struct.unpack('I', f.read(4))[0]

            #if args.verbose:
            #   print('\t[%d] #%08x' % (j, color))

for id_ in itertools.count():
    offset = f.tell()

    if offset == header[1]:
        print('LUT end at %d' % offset)
        break

    offset = struct.unpack('I', f.read(4))[0]

    if args.verbose and offset != 0:
        print('ID=%d offset=%d' % (id_, offset))

f.seek(8192, 1)
f.read(40)      # ???

while f.read(1):
    f.seek(-1, 1)

    offset = f.tell()
    print('@%d' % offset)

    entry_header = struct.unpack('IIII', f.read(16))

    entry_size = entry_header[1]

    print('offset1=%d entry_size=%d zero1=%d flags1=%08X' % entry_header)
    
    unk_header2 = struct.unpack('HHIIIII', f.read(24))
    has_name = unk_header2[5]
    id_ = unk_header2[6]
    print('unk1=%d unk2=%d unk3=%d unk4=%d has_name=%d ID=%d unk5=%08X' % unk_header2)

    if has_name:
        name = fftools.read_sz(f)
        print('\tname=%s' % name)

    f.seek(offset + 16 + entry_size)
