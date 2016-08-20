
files = {}
stack = []

def track(f, name):
    track = open('%s.xtr' % name, 'wt')
    files[f] = (name, track)
    print('%10s %10s %10s %10s %10s %10s %s' % ('begin', 'end', 'length', 'begin', 'end', 'length',
        'section'), file=track)

def begin(f, section_name):
    if not f in files:
        return

    stack.append((f, section_name, f.tell()))

def end(pad=0):
    f, section_name, begin = stack.pop()
    end = f.tell()

    insert(f, section_name, begin, end, pad)

def insert(f, section_name, begin, end, pad=0):
    if not f in files:
        return

    length = end - begin

    if pad:
        end = (end + pad - 1) // pad * pad

    print('%10d %10d %10d 0x%08X 0x%08X 0x%08X %s' % (begin, end, length, begin, end, length,
            section_name), file=files[f][1])

def parse(filename):
    with open(filename + '.xtr', 'rt') as f:
        # skip header
        f.readline()

        def parse_line(line):
            begin = int(line[0:10])
            end = int(line[11:21])
            name = line[66:]
            return (begin, end, name)

        return [parse_line(line.rstrip('\n')) for line in f]
