
def escape (text, characters):
    """ Escape the given characters from a string. """
    for character in characters:
        text = text.replace(character, '\\' + character)
    return text 


if __name__ == '__main__':
    print escape("ghjkl;\\\'", ["\\", "'" ])
    