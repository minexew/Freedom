import io, struct, zlib

def read_sz(f):
    s = ''

    while True:
        b = f.read(1)

        if not b or b == b'\x00':
            break

        if ord(b) >= 128:
            s += '\\x%02X' % ord(b)
        else:
            s += b.decode('ascii')

    return s

def open_compressed(filename, dump_uncompressed):
    f = open(filename, 'rb')

    header = struct.unpack('IIB', f.read(9))
    print('Compressed header: size=%d ends_at=%d compression=%02X' % (header[0], header[1], header[2]))

    stream = f.read(header[1] - f.tell())

    if header[2] == 0:      # DEFLATE-compressed
        data = zlib.decompress(stream, -15)

        if dump_uncompressed:
            open(filename + '.raw', 'wb').write(data)

        return io.BytesIO(data)
    elif header[2] == 1:
        return io.BytesIO(stream)
    else:
        raise('Unrecognized compression mode %02X!' % header[2])
