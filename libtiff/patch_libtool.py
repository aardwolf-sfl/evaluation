LIBTOOL = 'libtool'

PATTERN = '-l*)'

FIRST_OCC = '''    if test X-load = "X$arg"; then
        func_append compile_command " $arg"
        continue
    fi
'''

REST_OCC = '''    if test X-load = "X$deplib"; then
        continue
    fi
'''

with open(LIBTOOL) as fh:
    lines = fh.readlines()

n_occ = 0
output = ''

for line in lines:
    output += line

    if PATTERN in line:
        if n_occ == 0:
            output += FIRST_OCC
        else:
            output += REST_OCC

        n_occ += 1

with open(LIBTOOL, 'w') as fh:
    fh.write(output)
