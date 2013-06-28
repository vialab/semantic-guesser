import os.path

#def leopard(): #lol

def getAbsPath(path):
  if path.strip()[0] is '~':
    #in the case that there's a tilde in the path, abspath doesn't handle this right.
    return os.path.abspath(os.path.expanduser(path))
  else:
    return os.path.abspath(path)
