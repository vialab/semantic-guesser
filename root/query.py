

names = "SELECT dict_text FROM dictionary where dictset_id = 20 or dictset_id = 30;"


def segments(bounds=None, pass_ids=None):
    """ Returns all the segments.

    bounds - list of the form [offset, size]
    pass_ids - list of password ids whose segments will be fetched.
    If passed, bounds are ignored.

    """

    q = "SELECT sets.set_id AS set_id, " + \
        "set_contains.id AS set_contains_id, dict_text, dictset_id, " + \
        "pos, sentiment, synset, category, dictset_id, pass_text, s_index, e_index " + \
        "FROM set_contains LEFT JOIN sets ON set_contains.set_id = sets.set_id " + \
        "LEFT JOIN dictionary ON set_contains.dict_id = dictionary.dict_id "

    # include this to retrieve case sensitive password text.
    # after changing the parser to save case sensitive string in
    # sets.pass_text, we can abandon this line
    q += "LEFT JOIN passwords on sets.pass_id = passwords.pass_id "

    if pass_ids:
        return q + "WHERE sets.pass_id in ({})".format(str(pass_ids)[1:-1])

    if bounds:
        return q + "LIMIT {} OFFSET {}".format(bounds[1], bounds[0])
    else:
        return q




def max_pass_id():
    return "SELECT MAX(pass_id) as max FROM sets"