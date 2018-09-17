#!/usr/bin/env python

"""
Reads a list of cleartext passwords and encodes them using
John The Ripper's dummy format (username:$dummy$hexadecimal)
"""

import argparse
import sys
import binascii

def options():
	parser = argparse.ArgumentParser()
	parser.add_argument('file', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='list of passwords, one per line')
	return parser.parse_args()


if __name__ == "__main__":
	opts = options()

	for i, line in enumerate(opts.file):
		pwd = line.rstrip('\r\n')

		print('{}:$dummy${}'.format(i, binascii.hexlify(pwd.encode()).decode()))

	opts.file.close()
