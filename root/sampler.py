#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from random import sample, randint
from math import ceil
from argparse import ArgumentParser
import time
import query
import database
import sys
from util import printprogress, set_innodb_checks

def options():
    parser = ArgumentParser()
    parser.add_argument('password_set', default=1, type=int,
        help='the id of the collection of passwords to be sampled for testing')
    parser.add_argument('n', type=int, help='sample size (number of testing instances)')
    return parser.parse_args()

def pwset_bounds(conn, pwset):
    """ Returns the minimum and maximum pass_id from a group of passwords
    (determined by pwset_id) as a tuple of the form (min, max).
    """
    c = conn.cursor()
    c.execute(query.pwset_bounds(pwset))
    first_record = c.fetchone()
    max = first_record['max']
    min = first_record['min']
    return min, max

def get_ids(conn, pwset, n):
    "Randomly selects n ids within the range of a password set"
    min, max = pwset_bounds(conn, pwset)
    if min == None or max == None:
        msg = "Could not determine id range for password set {}."\
            " Are you sure this pw set exists in the db?".format(pwset)
        raise Exception(msg)
    return sample(range(min, max), n)

def mark_as_test(conn, pwset, ids):
    """ Marks list of ids as test instances on db.

    Uses strategy for fast bulk updating:
    1) Inserts all ids into temporary table.
    2) Updates passwords table (set test = 1) using a join with the temp table.

    @params:
        conn  - MySQLDb connection
        pwset - id of the password set
        ids   - ids of the records to be marked as test instances
    """

    # when performing bulk inserts, it is faster to insert rows
    # in PRIMARY KEY order
    ids = sorted(ids)

    t1 = time.time()
    cursor = conn.cursor()

    set_innodb_checks(cursor, False)

    # Reset all rows (test = 0)
    print "Reseting existing test instances... (This may take a while)"
    # cursor.execute("UPDATE passwords set test = 0 where pwset_id = {};"
    cursor.execute("UPDATE passwords set test = 0 where pwset_id = {} AND test = 1;"
        .format(pwset))
    conn.commit()

    try:
        print "Sending ids of testing instances to db (temp table)..."

        # Create temporary table where ids of test instances will be inserted
        tablename = "temp_" + str(randint(1,100000))
        cursor.execute("CREATE TABLE {} (pass_id int, PRIMARY KEY (pass_id))"
            .format(tablename))

        # Insert {segsize} rows at a time into temp table
        segsize = 10000
        i = 0
        max_iter = ceil(len(ids)/segsize)

        while i < max_iter:
            seg = ids[i * segsize : (i + 1) * segsize] # a segment of the ids array
            values = [ (id_,) for id_ in seg] # executemany accepts an array of tuples


            q = "INSERT INTO {} VALUES (%s)".format(tablename)
            cursor.executemany(q, values)
            cursor.execute("COMMIT;")

            printprogress(i, max_iter, prefix='Progress:',
                suffix = 'complete', barLength = 50)
            i += 1

        ids = []

        # Join table passwords with temp table and set test = 1
        print "\nUpdating test instances on production table (join)"
        print "(This will likely take a while)..."
        q = "UPDATE passwords INNER JOIN {} USING(pass_id) SET passwords.test = 1" \
            .format(tablename)
        cursor.execute(q);
        conn.commit()

    except KeyboardInterrupt:
        print "\nExecution cancelled by user."
    finally:
        # interrupt current query with no guarantees and terminate execution
        conn.close() # close connection abruptly
        newconn = database.connection()
        newcursor = newconn.cursor()
        newcursor.execute("DROP TABLE {}".format(tablename)) # drop temp table
        set_innodb_checks(newcursor, True) # cancel performance tricks
        print "Elapsed time: {} minutes.".format((time.time()-t1)/60)
        newconn.close()
        #sys.exit(0)


def sample_passwords(pwset, n):
    conn = database.connection()
    testing_ids = get_ids(conn, pwset, n)
    mark_as_test(conn, pwset, testing_ids)

if __name__ == "__main__":
    opts = options()
    sample_passwords(opts.password_set, opts.n)
