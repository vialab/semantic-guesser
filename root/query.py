

def fragments(bounds=None):
    """ Returns all the fragments.
    
    bounds - array of the form [offset, size]
    """
    q = "SELECT sets.set_id AS set_id, " + \
            "set_contains.id AS set_contains_id, dict_text, dictset_id, " + \
            "pos, sentiment, synset, category, dictset_id " + \
            "FROM set_contains LEFT JOIN sets ON set_contains.set_id = sets.set_id " +\
            "LEFT JOIN dictionary ON set_contains.dict_id = dictionary.dict_id "
    if bounds:
        return q + "LIMIT {} OFFSET {}".format(bounds[1], bounds[0])
    else:
        return q
        
        