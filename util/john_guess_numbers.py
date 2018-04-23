"""
Reads john.log and extracts the guess number of each cracked password.

john.conf should have LogCrackedPasswords = Y

Example:
./john --format=dummy ~/Dropbox/Data/yahoo/dummy_passwords.txt --session=test2 --pot=test2.pot

python3 john_guess_numbers.py test2.log
"""

import argparse
import re

def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('log_file')
    return parser.parse_args()

if __name__ == '__main__':
    opts = options()

    with open(opts.log_file) as f:

        # lines follow this format:
        # 0:00:00:01 + Cracked 361383: 445857445857 as candidate #487839

        prev_password = None # prevent output of duplicates

        for line in f:
            matches = re.findall("\+ Cracked .+: (.+) as candidate #(\d+)", line)
            if len(matches):
                password, guess_number = matches[0]
                if password != prev_password:
                    print("{}\t{}".format(password, guess_number))
                prev_password = password
