from context import pos, train


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

    print(train.pos_tag(['1','q','2','w','3','e','4','r'], tagger))


test_strings = ["sin0246810", "786fr76d7d7", "wsF1eY49nQAJ", "111aaa", "kamong89561130", "63mxARjA0Ngl85Eq", "rocsika1", "oLa15987456", "lbdesiempre89", "aSltoJo33", "Surround12#", "fDSdyaDcyMQXiff8", "Carlos_1234", "4547635ab", "p@5sword", "mhpvnit1", "DPYdpy666", "5y96sstu", "sxp2010735462", "k1ttyfl1p", "fr33k1ck", "leguc152", "10971097A", "7lsZ1ABzzhF", "ix3skippi", "hqbazmxk4", "volina1", "bolets459802", "oyfzetkca472", "h0ripatter", "numa1100", "q963258741q", "EDWINwijaya110700", "ji123456", "batuhan123", "Prestige1", "diana123melahizo", "sasd0009", "a100121", "lafamille225", "xbox360", "666gato", "queenie4", "Cv2kLH7E2K1", "OVL60WjcyNQNdRqm", "lamisma*963.", "fakelight0271856940", "webhost230788", "credit..52", "vjy291", "blablashow12", "laongoandong35", "datamore1562", "iox4v9s", "ubkrqmx14", "fe12li34pe", "lMi64909", "aaa21478963", "IpA3JcDo3P1", "Teskrel135", "aê(Ã,?k", "oEG6oC60MV", "rsqjcmh5", "inonoho704", "yunanobe1978", "golfver6", "niyazi123", "a8800886429", "s29608939", "4kexi34vb2", "asad354", "4lice1966", "afcp2706", "bA4hHAjEzMAq126m", "36redsoxfan", "september242008", "qN8Ix3Vt7UOQtG", "borsetica1", "diki3805", "qweasdzxc123", "kranos76", "Ramjane123", "cupor911", "qazwsxedc1", "mertcan123", "fitnabook786", "zhBqPsjE5NQvoUDq", "512250057a", "huwot640", "a111111", "erka22", "54425375a", "kouek00", "oxe2p4e", "q12930qq", "ffz80uq", "rm0Z4RDc5Mwe6V6c", "Soporte11", "lourd69", "Kellionna<3"]



def test_chunk_and_pos():
    tagger = pos.BackoffTagger.from_pickle()
    blacklist=train.POSBlacklist()
    for s in test_strings:
        chunks = train.getchunks(s)
        print(s, end=' ')
        for chunk, tag in train.pos_tag(chunks, tagger, blacklist):
            print("{} ({})".format(chunk, tag), end=' ')
        print()


# test_tag_random_string()
test_chunk_and_pos()
