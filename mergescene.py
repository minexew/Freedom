
import csv, sys

prm_dir = sys.argv[1] + '_prm'

def transform(mtx, v):
    '''return (
        v[0] * mtx[0] + v[1] * mtx[1] + v[2] * mtx[2],
        v[0] * mtx[3] + v[1] * mtx[4] + v[2] * mtx[5],
        v[0] * mtx[6] + v[1] * mtx[7] + v[2] * mtx[8])'''
    '''return (
        v[0] * mtx[2] + v[1] * mtx[5] + v[2] * mtx[8],
        v[0] * mtx[1] + v[1] * mtx[4] + v[2] * mtx[7],
        v[0] * mtx[0] + v[1] * mtx[3] + v[2] * mtx[6])'''
    return (
        v[0] * mtx[2] + v[1] * mtx[1] + v[2] * mtx[0],
        v[0] * mtx[5] + v[1] * mtx[4] + v[2] * mtx[3],
        v[0] * mtx[8] + v[1] * mtx[7] + v[2] * mtx[6])

with open(sys.argv[1] + '.instances') as f, open(prm_dir + '/00scene.obj', 'wt') as output:
    r = csv.reader(f)

    index_offset = 0

    for entry in r:
        if not len(entry): continue

        objfile = prm_dir + '/%s.obj' % entry[1]

        try:
            with open(objfile) as obj_in:
                num_vertices = 0
                pos = list(map(float, entry[2:5]))
                mtx = list(map(float, entry[5:14]))

                for line in obj_in:
                    tokens = line.rstrip('\n').split()

                    if tokens[0] == 'f':
                        indices = list(map(int, tokens[1:4]))
                        print('f %d %d %d' % (index_offset + indices[0], index_offset + indices[1], index_offset + indices[2]), file=output)
                    elif tokens[0] == 'l':
                        indices = list(map(int, tokens[1:3]))
                        print('l %d %d' % (index_offset + indices[0], index_offset + indices[1]), file=output)
                    elif tokens[0] == 'o':
                        print('o %s/%s' % (entry[0], tokens[1]), file=output)
                    elif tokens[0] == 'v':
                        v = transform(mtx, list(map(float, tokens[1:4])))
                        print('v %g %g %g' % (pos[0] + v[0], pos[1] + v[1], pos[2] + v[2]), file=output)
                        num_vertices += 1
                    else:
                        print(line.rstrip('\n'), file=output)

                index_offset += num_vertices
        except FileNotFoundError:
            print('Warning: couldn\'t open', objfile)
