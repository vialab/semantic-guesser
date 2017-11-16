from context import pos


def test_backoff_tagger():
    tagger = pos.BackoffTagger()
    tags1 = tagger.tag(['i', 'love', 'you'])

    # tagging works
    assert len(tagger.tag(['i', 'love', 'you'])) == 3

    # pickling works
    tagger.pickle()
    tagger_from_pickle = pos.BackoffTagger.from_pickle()
    tags2 = tagger_from_pickle.tag(['i', 'love', 'you'])

    for i in range(len(tags2)):
        assert tags1[i][1] == tags2[i][1]


def test_tag_random_string():
    tagger = pos.BackoffTagger.from_pickle()
    print(tagger.tag(['1','q','2','w','3','e','4','r']))


test_tag_random_string()
