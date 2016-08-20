#!/usr/bin/env python3

import argparse, os, struct, sys
import fftools

parser = argparse.ArgumentParser()
parser.add_argument('zgffile')
parser.add_argument('-v', dest='verbose', action='store_true')
args = parser.parse_args()

f = fftools.open_compressed(args.zgffile, False)

dump_dir = os.path.splitext(args.zgffile)[0] + '_zgf'
os.makedirs(dump_dir, exist_ok=True)

tfgz_header = struct.unpack('4sIIIII', f.read(24))
print('TFGZ header: %s unk=%08X ends_at=%d count=%d unk=%08X unk=%08X' % tfgz_header)

count = tfgz_header[3]

sizes = []

for i in range(count):
    size = struct.unpack('I', f.read(4))[0]
    print(size)
    sizes += [size]

for i in range(count):
    data = f.read(sizes[i] - 24)
    name = fftools.read_sz(f)
    print(f.tell())

    dump_path = os.path.join(dump_dir, name)
    os.makedirs(os.path.dirname(dump_path)[0], exist_ok=True)
    open(dump_path, 'wb').write(data)
    break
