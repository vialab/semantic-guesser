#!/usr/local/bin/python
# coding: utf-8

import os
import sys
import time
import logging

class Timer:

    def __init__(self, title=None, logger=None):
        self.title = title
        self.logger = logger if logger is not None else logging.getLogger(__name__)

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.elapsed = self.end - self.start

        if self.elapsed < 60:
            unit = "seconds"
            figure = self.elapsed
        elif self.elapsed < 60*60:
            unit = "minutes"
            figure = self.elapsed/60
        else:
            unit = "hours"
            figure = self.elapsed/60*60

        message = "Time elapsed while {}: {:.1f} {}"\
            .format(self.title, figure, unit)
        self.logger.info(message)

# if __name__ == '__main__':
#     with Timer('test'):
#         time.sleep(2)

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
