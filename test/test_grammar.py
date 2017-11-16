from context import Grammar


def test_tagging():
    g = Grammar()

    chunk = ('love', 'v', 'love.n.01')
    assert g._tag_semantic_backoff_pos(*chunk) == 'love.n.01'
    assert g._tag_pos_semantic(*chunk) == 'v_love.n.01'
    assert g._tag_pos(*chunk) == 'v'

    chunk = ('trampolining', 'v', None)
    assert g._tag_semantic_backoff_pos(*chunk) == 'v'
    assert g._tag_pos_semantic(*chunk) == 'v_unkwn'
    assert g._tag_pos(*chunk) == 'v'

    chunk = ('usa', 'np', 'country.n.01')
    assert g._tag_semantic_backoff_pos(*chunk) == 'country'
    assert g._tag_pos_semantic(*chunk) == 'np_country.n.01'
    assert g._tag_pos(*chunk) == 'np'

    chunk = ('3u4h3u4', None, None)
    assert g._tag_semantic_backoff_pos(*chunk) == 'mixed7'
    assert g._tag_pos_semantic(*chunk) == 'mixed7'
    assert g._tag_pos(*chunk) == 'mixed7'

    chunk = ('ahshauhdad', None, None)
    assert g._tag_semantic_backoff_pos(*chunk) == 'char10'
    assert g._tag_pos_semantic(*chunk) == 'char10'
    assert g._tag_pos(*chunk) == 'char10'

    chunk = ('121312', None, None)
    assert g._tag_semantic_backoff_pos(*chunk) == 'number6'
    assert g._tag_pos_semantic(*chunk) == 'number6'
    assert g._tag_pos(*chunk) == 'number6'



test_tagging()
