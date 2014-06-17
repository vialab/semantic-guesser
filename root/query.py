

names = "SELECT dict_text FROM dictionary where dictset_id = 20 or dictset_id = 30;"


def segments(pwset_id, bounds=None, pass_ids=None):
    """ Returns all the segments.

    pwset_id - the id of the password set to be gathered
    bounds - list of the form [offset, size]
    pass_ids - list of password ids whose segments will be fetched.
        If passed, bounds are ignored.

    """

    q = "SELECT sets.set_id AS set_id, " + \
        "set_contains.id AS set_contains_id, dict_text, dictset_id, " + \
        "pos, sentiment, synset, category, dictset_id, pass_text, s_index, e_index " + \
        "FROM set_contains LEFT JOIN sets ON set_contains.set_id = sets.set_id " + \
        "LEFT JOIN dictionary ON set_contains.dict_id = dictionary.dict_id "

    # included this to retrieve case sensitive password text (pass_text).
    # it is also useful for filtering by pwset_id
    q += "LEFT JOIN passwords on sets.pass_id = passwords.pass_id " + \
        "WHERE passwords.pwset_id = {}".format(pwset_id)

    if pass_ids:
        return q + "AND sets.pass_id in ({})".format(str(pass_ids)[1:-1])

    if bounds:
        return q + "LIMIT {} OFFSET {}".format(bounds[1], bounds[0])
    else:
        return q


def n_sets(pwset_id):
    """ Retrieves the number of sets (segmentations) associated with a certain group
    of passwords.

    pwset_id - the id of the target group of passwords
    """

    return "SELECT COUNT(*) as count FROM sets LEFT JOIN passwords on sets.pass_id = passwords.pass_id " \
           "WHERE passwords.pwset_id = {}".format(pwset_id)


def extent_parsed(pwset_id):
    """ Returns the SQL string to query the minimum and maximum pass_id (that have been parsed)
        from a group of passwords (determined by pwset_id). If no passwords have been parsed
        from the group, this query will return empty.
    """
    return "SELECT MAX(pass_id) as max, MIN(pass_id) as min FROM sets LEFT JOIN passwords on sets.pass_id = passwords.pass_id " \
            "WHERE passwords.pwset_id = {}".format(pwset_id)