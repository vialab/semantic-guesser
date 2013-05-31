
import os

def abspath(path):
    """ Returns the absolute path for a file relative of the
    location from which the module was loaded (usually root).
    This method allows you to load an internal file independent
    of the location the program was called from. 
    """
    dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir, path)