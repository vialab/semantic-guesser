#!/usr/local/bin/python
# coding: utf-8

import os
import sys

def dbcredentials():
    f = open(abspath('db_credentials.conf'))

    credentials = dict()

    for line in f:
        key, value = line.split(':', 1)
        credentials[key.strip()] = value.strip()

    return credentials

def set_innodb_checks(cursor, ischecked):
    cursor.execute("SET autocommit = {};".format(int(ischecked)))
    cursor.execute("SET unique_checks = {};".format(int(ischecked)))
    cursor.execute("SET foreign_key_checks = {};".format(int(ischecked)))

def abspath(path):
    """ Returns the absolute path for a file relative of the
    location from which the module was loaded (usually root).
    This method allows you to load an internal file independent
    of the location the program was called from.
    """
    dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir, path)

# Print iterations progress
# From http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def printprogress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr = "{0:." + str(decimals) + "f}"
    percent = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percent, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def values_sorted_by_key(dictionary):
    return map(lambda x : x[1], sorted(dictionary.items()))
