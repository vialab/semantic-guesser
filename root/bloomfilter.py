"""
Creates a BloomFilter with a certain capacity
adds N1 passwords from a list to it.
For each password in a second list, checks its
membership in the first set using the BlooomFilter.
Outputs the result of each check (0 or 1) to stdout.

Author: Rafael Veras

"""

import pybloom_live as pybloom
import math
import argparse

# number of lines to be read from first list
CAPACITY = 8e9

# false positive rate we are willing to accept
ERROR_RATE = 1e-6


def opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('file1', type=argparse.FileType('r'))
    parser.add_argument('file2', type=argparse.FileType('r'))
    return parser.parse_args()


def sizeof_fmt(num, suffix='B'):
    """Format size in bits to human readable text."""

    num /= 8 # to bytes
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def memory_requirement():
    """
    Calculate how much RAM is needed, according to
    formulas from https://en.wikipedia.org/wiki/Bloom_filter.

    Return figure in GB.
    """
    return - CAPACITY * math.log(ERROR_RATE) / (math.log(2) ** 2)


print "This execution will require {} RAM".format(sizeof_fmt(memory_requirement()))
print "If RAM is not sufficient, increase the ERROR_RATE or reduce CAPACITY."
print "Current values: \nCAPACITY: {:d}\nERROR_RATE: {:f}\n".format(int(CAPACITY), ERROR_RATE)

args = opts()

filtro = pybloom.BloomFilter(capacity=CAPACITY, error_rate=ERROR_RATE)

for i, line in enumerate(args.file1):
    if i >= CAPACITY: 
        break

    pwd = line.strip()
    filtro.add(pwd)

print "{:,} lines read from File 1.".format(i+1)

matches = 0

for i, line in enumerate(args.file2):
    if i >= CAPACITY: 
        break

    pwd = line.rstrip()
    if pwd in filtro:
        matches += 1

print "{:,} lines read from File 2\n".format(i+1)

print "{} passwords were found in both files.".format(matches)
print "Count minus expected false positives: {:d}".format(int(math.ceil(matches*(1-ERROR_RATE))))

#TODO: Create BloomFilter instance.
#TODO: Read file, compare..
