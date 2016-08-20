#!/usr/bin/env python3

'''
GMS format description:
- entire file is wrapped in a compression wrapper

Header
======

(0-15)
u32     instances_offset
u32     imports_offset
u32     offset3
u32     count

(16-31)
u32     offset4
u32     offset5
u32     offset6
u32     length7

...more unknowns...

Instance table
==============

u32 count

repeat(count) {
    u16 instance            // position of INSTANCE in decompressed file, divided by 4
    u16 unk1
    u16 unk2
    u16 unk3
}

INSTANCE structure
==================

u32     buf_offset          // SZ(name) pos in BUF file
u32     mtx_offset
    ->  float[3][3] transform

u32     pos_offset
    ->  float[3] pos

u32     PRM_offset
    ->  ????

u32     unk_flags

u32     stringlist_offset or 0
    ->  u32 count
        repeat(count) {
            uint32_t    function_name_pos   // SZ(function_name) pos in stream
            float       unk
        }


u32     unk_flags

u32     auxbuf_offset_in_BUF_file or 0
    ->  u32 unk
        u16 size
        u16 flags
        u32 size
        u32 num_entries

        repeat(num_entries) {
            u32 fourcc
            u16 entry_length
            u16 flags
            u8[entry_length - 8] data
        }

u32     record_offset
    ->  u32 length
        u8[length] data

u32     zero

u16[4]  unk

Import table
============

u32 count

repeat(count) {
    u32 name_offset         // SZ(function name) pos in stream
}


'''

import argparse, io, os, struct, sys, zlib
import fftools, xtr

parser = argparse.ArgumentParser()
parser.add_argument('gmsfile')
parser.add_argument('-v', dest='verbose', action='store_true')
args = parser.parse_args()

def parse_auxbuf():
    offset = buf_f.tell()
    xtr.begin(buf_f, 'auxbuf_%d' % offset)
    data = struct.unpack('IHHII', buf_f.read(16))
    print('\t\t\tzero=%d size=%d flags=%X size=%d num_entries=%d' % data)
    num_entries = data[4]

    dump_auxbuf = False

    for i in range(num_entries):
        data = struct.unpack('4sHH', buf_f.read(8))
        entry_length = data[1]
        print('\t\t\t\t%s (%d bytes, %04X flags)' % data)

        if not dump_auxbuf:
            buf_f.seek(entry_length - 8, os.SEEK_CUR)
        else:
            auxbuf_text = buf_f.read(entry_length - 8)

            with open('dumps/auxbuf_%d_%d' % (offset, i), 'wb') as auxbuf_dump:
                auxbuf_dump.write(auxbuf_text)

    xtr.end()

def parse_instance():
    instance_offset = f.tell()
    data = struct.unpack('II', f.read(8))
    buf_offset = data[0]
    mtx_offset = data[1]

    buf_f.seek(buf_offset)
    xtr.begin(buf_f, 'instance_%d_name' % instance_offset)
    name = fftools.read_sz(buf_f)
    xtr.end(4)
    print('\t"%s"' % name)

    offset = f.tell()
    print('\t\tmtx = [at %d](' % mtx_offset)
    f.seek(mtx_offset)
    mtx = [None, None, None]
    for i in range(3):
        mtx[i] = struct.unpack('fff', f.read(12))
        print('\t\t\t(%+4.2f %+4.2f %+4.2f)' % mtx[i])
    print('\t\t)')
    f.seek(offset)

    data = struct.unpack('II', f.read(8))
    pos_offset = data[0]
    PRM_offset = data[1]

    offset = f.tell()
    f.seek(pos_offset)
    pos = struct.unpack('fff', f.read(12))
    print('\t\tpos = [%d](%+4.2f %+4.2f %+4.2f)' % (pos_offset, pos[0], pos[1], pos[2]))
    f.seek(offset)

    print('\t\tPRM_offset=%08X (%d)' % (PRM_offset, PRM_offset))

    if PRM_offset:
        print('%s,%d,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g' % (name, PRM_offset, pos[0], pos[1], pos[2],
                mtx[0][0], mtx[0][1], mtx[0][2], mtx[1][0], mtx[1][1], mtx[1][2], mtx[2][0], mtx[2][1], mtx[2][2]), file=instances_list)

    data = struct.unpack('II', f.read(8))
    print('\t\t%08X stringlist_offset=%08X' % (data[0], data[1]), end='\t')
    stringlist_offset = data[1]

    if stringlist_offset:
        offset = f.tell()
        f.seek(stringlist_offset)
        xtr.begin(f, 'stringlist_%d' % offset)
        num_entries = struct.unpack('I', f.read(4))[0]
        print('%d strings @ %d' % (num_entries, stringlist_offset))

        pairs = [struct.unpack('If', f.read(8)) for i in range(num_entries)]
        xtr.end()

        for i, (str_offset, unk) in enumerate(pairs):
            f.seek(str_offset)
            xtr.begin(f, 'stringlist_%d/%d' % (offset, i))
            s = fftools.read_sz(f)
            xtr.end(4)
            print('\t\t\t("%s"\t%4.2f)' % (s, unk))

        f.seek(offset)
    else:
        print()

    data = struct.unpack('II', f.read(8))
    print('\t\t%08X auxbuf_offset=%08X' % (data[0], data[1]))
    auxbuf_offset = data[1]

    if auxbuf_offset:
        print('\t\taux buf @ %d:' % auxbuf_offset)
        buf_f.seek(auxbuf_offset)
        parse_auxbuf()

    data = struct.unpack('II', f.read(8))
    print('\t\trecord_offset=%08X %08X' % (data[0], data[1]), end='\t')
    record_offset = data[0]

    dump_record = False

    if record_offset:
        offset = f.tell()
        f.seek(record_offset)
        record_length = struct.unpack('I', f.read(4))[0]
        print('(%d-byte record @ 0x%x-0x%x)' % (record_length, record_offset, record_offset + 4 + record_length))
        xtr.insert(f, 'instance_%d_record' % instance_offset, record_offset, record_offset + 4 + record_length, 4)

        if dump_record:
            record = f.read(record_length)

            with open('dumps/record_%d' % (offset), 'wb') as record_dump:
                record_dump.write(record)

        f.seek(offset)
    else:
        print()

    data = struct.unpack('HHHH', f.read(8))
    print('\t\t%04X %04X %04X %04X' % (data[0], data[1], data[2], data[3]))
    print('\t\tend@%d (0x%x)' % (f.tell(), f.tell()))
    print()

    #sys.exit(0)

def parse_import_table():
    xtr.begin(f, 'imports')
    print('import table:\t(at %d / %Xh)' % (f.tell(), f.tell()))
    count = struct.unpack('I', f.read(4))[0]
    print(count, 'entries')

    display = True

    if display: print('\tindex\tname_p\tname')

    for i in range(count):
        xtr.begin(f, 'imports/%d' % i)

        data = struct.unpack('I', f.read(4))[0]

        offset = f.tell()
        f.seek(data)
        xtr.begin(f, 'import_%d_name' % i)
        text = fftools.read_sz(f)
        xtr.end(4)
        f.seek(offset)

        if display: print('\t(%d)\t%d\t%s' % (i, data, text))

        xtr.end()

    print('import table ends at (%d / %Xh)' % (f.tell(), f.tell()))
    print()
    xtr.end()

def parse_instance_table():
    xtr.begin(f, 'instances')
    print('instance table:\t(at %d / %Xh)' % (f.tell(), f.tell()))
    count = struct.unpack('I', f.read(4))[0]
    print(count, 'entries')

    for i in range(count):
        xtr.begin(f, 'instances/%d' % i)
        data = struct.unpack('IHH', f.read(8))
        instance_off = data[0] * 4
        print('  index=%d instance_off=%d / 0x%x unk=(%04X %04X)' % (i, instance_off, instance_off, data[1], data[2]))

        offset = f.tell()
        f.seek(instance_off & 0x00FFFFFF)
        parse_instance()
        f.seek(offset)
        xtr.end()

    print('instance table ends at (%d / %Xh)' % (f.tell(), f.tell()))
    print()
    xtr.end()

def parse_offset4():
    xtr.begin(f, 'offset4_table')
    print('offset4 table:\t(%d / %Xh)' % (f.tell(), f.tell()))
    count = struct.unpack('I', f.read(4))[0]
    print("  rows=%d" % count)

    for i in range(count):
        data = struct.unpack('HHHHHH', f.read(12))
        print('  ', data)
    print('offset4 table ends at (%d / %Xh)' % (f.tell(), f.tell()))
    print()
    xtr.end()

def parse_offset5():
    xtr.begin(f, 'offset5_table')
    print('offset5 table:\t(%d / %Xh)' % (f.tell(), f.tell()))

    count = struct.unpack('I', f.read(4))[0]
    print("rows = %4d" % count)

    for row in range(count):
        for i in range(24):
            print("%4d" % struct.unpack('I', f.read(4)), end ='')
        print()
    #print('\noffset5 table ends at (%d / %Xh)' % (f.tell(), f.tell()))
    xtr.end()

def parse_offset6():
    offset = f.tell()
    print('offset6 table:\t(%d / %Xh)' % (offset, offset))

    size = struct.unpack('I', f.read(4))[0]
    print("  size=%d" % size)
    things = struct.unpack('IIII', f.read(16))
    count1 = things[0]
    print("  (%d %d %d %08X)" % things)
    xtr.insert(f, 'offset6_table', offset, offset + 4 + size)

    stuff1 = [struct.unpack('I', f.read(4))[0] for i in range(count1 - 5)]

    for row in range((len(stuff1) + 7) // 8):
        if row * 8 + 8 <= len(stuff1): count = 8
        else: count = len(stuff1) - row * 8

        print('    ' + ' '.join(['%08X' % stuff1[row * 8 + i] for i in range(count)]))

    unksize = struct.unpack('I', f.read(4))[0]
    print("  unksize=%d" % unksize)

    print('now at %d' % f.tell())
    print('    %f %f %f' % struct.unpack('fff', f.read(12)))

    #objfile = open('dumps/offset6.obj', 'wt')

    while f.tell() < offset + 4 + size:
        whatt = struct.unpack('I', f.read(4))[0]
        #print('    %f' % struct.unpack('f', f.read(4))[0])
        print('    %d' % whatt)

        if whatt != 0:
            print('    %08X %08X %08X %08X %08X %08X' % struct.unpack('IIIIII', f.read(24)))
            print('    %08X %08X %08X %08X %08X %08X' % struct.unpack('IIIIII', f.read(24)))

        vertex_data = struct.unpack('fffffffff', f.read(36))
        #print('v %f %f %f\nv %f %f %f\nv %f %f %f\nf -1 -2 -3' % vertex_data, file=objfile)

        print('    (%f %f %f) (%f %f %f) (%f %f %f)' % vertex_data)




        #print('    %f %f %f %f %f %f %f %f' % struct.unpack('ffffffff', f.read(32)))
        #print('  - %08X %08X %08X %08X %08X %08X %08X %08X' % struct.unpack('IIIIIIII', f.read(32)))
        #print('    %08X %08X %08X %08X %08X %08X %08X %08X' % struct.unpack('IIIIIIII', f.read(32)))
        #print('    %08X %08X %08X %08X' % struct.unpack('IIII', f.read(16)))
        #print('    (%f %f %f) %08X %08X %08X %08X %08X' % struct.unpack('fffIIIII', f.read(32)))
        #f.seek(112, os.SEEK_CUR)

    print('offset6 table ends at (%d / %Xh)' % (f.tell(), f.tell()))
    print()

f = fftools.open_compressed(args.gmsfile, False)
xtr.track(f, args.gmsfile)

try:
    buf_fname = os.path.splitext(args.gmsfile)[0] + '.BUF'
    buf_f = open(buf_fname, 'rb')
    xtr.track(buf_f, buf_fname)
except FileNotFoundError:
    print('Warning: unable to open ' + os.path.splitext(args.gmsfile)[0] + '.BUF')

instances_list = open(os.path.splitext(args.gmsfile)[0] + '.instances', 'wt')

xtr.begin(f, 'header')

scene_header = struct.unpack('IIII', f.read(16))

instances_offset = scene_header[0]

print('GameScene header: instances_offset=%d imports_offset=%d offset3=%d count=%d' % scene_header)

unk = struct.unpack('IIII', f.read(16))
offset4 = unk[0]
offset5 = unk[1]
offset6 = unk[2]
print('offset4=%d offset5=%d offset6=%d length7=%d' % unk)
unk = struct.unpack('IIII', f.read(16))
print('unk %s' % str(unk))
unk = struct.unpack('HHHHHHHH', f.read(16))
print('unk %s' % str(unk))

xtr.end()

f.seek(scene_header[1])
parse_import_table()

f.seek(instances_offset)
parse_instance_table()

f.seek(offset4)
parse_offset4()

f.seek(offset5)
parse_offset5()

f.seek(offset6)
parse_offset6()
