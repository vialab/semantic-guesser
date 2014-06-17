
import os

def dbcredentials():
    f = open(abspath('db_credentials.conf'))

    credentials = dict()

    for line in f:
        key, value = line.split(':')
        credentials[key.strip()] = value.strip()

    return credentials


def abspath(path):
    """ Returns the absolute path for a file relative of the
    location from which the module was loaded (usually root).
    This method allows you to load an internal file independent
    of the location the program was called from. 
    """
    dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir, path)
