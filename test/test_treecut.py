from context import _li_abe, li_abe, WordNetTreeNode, DefaultTree,\
    MleEstimator, LaplaceEstimator

def test_description_length():
    # --------------------------------------------------------
    # Comparing the results with Table 4 of Li & Abe (1998).
    # --------------------------------------------------------
    cut1  = [('ANIMAL', 10, 7)]
    cut2  = [('BIRD', 8, 4), ('INSECT', 2, 3)]
    cut3  = [('BIRD', 8, 4), ('bug', 0, 1), ('bee', 2, 1), ('insect', 0, 1)]
    cut4  = [('swallow', 0, 1), ('crow', 2, 1), ('eagle', 2, 1), ('bird', 4, 1), ('INSECT', 2, 3)]
    cut5  = [('swallow', 0, 1), ('crow', 2, 1), ('eagle', 2, 1), ('bird', 4, 1),
             ('bug', 0, 1), ('bee', 2, 1), ('insect', 0, 1)]

    cuts = [cut1, cut2, cut3, cut4, cut5]
    true_pdl = [    0,  1.66,  4.98,  6.64,  9.97]
    true_ddl = [28.07, 26.39, 23.22, 22.39, 19.22]
    true_dl  = [pdl + ddl for pdl, ddl in zip(true_pdl, true_ddl)]

    test_pdl = []
    test_ddl = []
    test_dl  = []

    for cut in cuts:
        _cut = []
        for tuple_ in cut:
            node = WordNetTreeNode(tuple_[0], value=tuple_[1])
            node.leaf_count = tuple_[2]
            _cut.append(node)

        test_pdl.append(_li_abe.compute_pdl(_cut, 10))
        test_ddl.append(_li_abe.compute_ddl(_cut, 10))
        test_dl.append(_li_abe.compute_dl(_cut, 10))

    assert all([abs(true - test) < 0.01 for true, test in zip(true_pdl, test_pdl)])
    assert all([abs(true - test) < 0.01 for true, test in zip(true_ddl, test_ddl)])
    assert all([abs(true - test) < 0.01 for true, test in zip(true_dl, test_dl)])


def test_dl_with_nodes():
    ANIMAL = WordNetTreeNode('ANIMAL')
    BIRD = WordNetTreeNode('BIRD')
    INSECT = WordNetTreeNode('INSECT')
    bug = WordNetTreeNode('bug', value=0)
    bee = WordNetTreeNode('bee', value=2)
    insect = WordNetTreeNode('insect', value=0)
    swallow = WordNetTreeNode('swallow', value=0)
    crow = WordNetTreeNode('crow', value=2)
    eagle = WordNetTreeNode('eagle', value=2)
    bird = WordNetTreeNode('bird', value=4)

    ANIMAL.add_child(BIRD)
    ANIMAL.add_child(INSECT)
    for child in [bug, bee, insect]: INSECT.add_child(child)
    for child in [swallow, crow, eagle, bird]: BIRD.add_child(child)

    ANIMAL.updateCounts()

    assert ANIMAL.value == 10
    assert ANIMAL.leaf_count == 7

    tree = DefaultTree(ANIMAL)

    cut = li_abe.findcut(tree)
    assert len(cut) == 2
    assert cut[0].key == 'BIRD'
    assert cut[1].key == 'INSECT'

    # test estimators
    mle = MleEstimator(ANIMAL.value)
    laplace = LaplaceEstimator(ANIMAL.value, ANIMAL.leaf_count, 1)
    assert mle.probability(eagle) == 0.2
    assert laplace.probability(eagle) == 3/17
    assert laplace.probability(BIRD) == 12/17

    total_prob = 0
    for node in ANIMAL.flat():
        if node.is_leaf():
            total_prob += laplace.probability(node)
    assert total_prob == 1

    cut_mle = li_abe.findcut(tree, mle)
    assert len(cut_mle) == 2
    assert cut_mle[0].key == 'BIRD'
    assert cut_mle[1].key == 'INSECT'


def test_laplace_estimator():
    cut1  = [('ANIMAL', 10, 7)]
    cut2  = [('BIRD', 8, 4), ('INSECT', 2, 3)]
    cut3  = [('BIRD', 8, 4), ('bug', 0, 1), ('bee', 2, 1), ('insect', 0, 1)]
    cut4  = [('swallow', 0, 1), ('crow', 2, 1), ('eagle', 2, 1), ('bird', 4, 1), ('INSECT', 2, 3)]
    cut5  = [('swallow', 0, 1), ('crow', 2, 1), ('eagle', 2, 1), ('bird', 4, 1),
             ('bug', 0, 1), ('bee', 2, 1), ('insect', 0, 1)]

    cuts = [cut1, cut2, cut3, cut4, cut5]

    laplace = LaplaceEstimator(10, 7, 1)

    for cut in cuts:
        _cut = []
        for tuple_ in cut:
            node = WordNetTreeNode(tuple_[0], value=tuple_[1])
            node.leaf_count = tuple_[2]
            _cut.append(node)

        # print(_li_abe.compute_pdl(_cut, 10))
        print(_cut)
        print(_li_abe.compute_ddl(_cut, 10, laplace))
        print(_li_abe.compute_dl(_cut, 10, laplace))
        print('---------')


# test_laplace_estimator()
