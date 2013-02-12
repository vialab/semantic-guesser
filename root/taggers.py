from nltk.tag import NgramTagger, SequentialBackoffTagger
from nltk.corpus import wordnet, names
from nltk.probability import FreqDist
import csv
from root.tagset_conversion import TagsetConverter
from sentiwordnet import SentiWordNetCorpusReader, SentiSynset
from nltk.corpus import wordnet as wn
from nltk.stem import PorterStemmer
from sets import Set

class QuadgramTagger(NgramTagger):
	def __init__(self, *args, **kwargs):
		NgramTagger.__init__(self, 4, *args, **kwargs)

class WordNetTagger(SequentialBackoffTagger):
	'''
	>>> wt = WordNetTagger()
	>>> wt.tag(['food', 'is', 'great'])
	[('food', 'NN'), ('is', 'VB'), ('great', 'JJ')]
	'''
	def __init__(self, *args, **kwargs):
		SequentialBackoffTagger.__init__(self, *args, **kwargs)
		
		self.wordnet_tag_map = {
			'n': 'NN',
			's': 'JJ',
			'a': 'JJ',
			'r': 'RB',
			'v': 'VB'
		}
	
	def choose_tag(self, tokens, index, history):
		word = tokens[index]
		if word is None :
			return None
		fd = FreqDist()
		
		for synset in wordnet.synsets(word):
			fd.inc(synset.pos)
		try :
			return self.wordnet_tag_map.get(fd.max())
		except : # in case fd is empty
			return None

class NamesTagger(SequentialBackoffTagger):
	'''
	>>> nt = NamesTagger()
	>>> nt.tag(['Jacob'])
	[('Jacob', 'NNP')]
	'''
	def __init__(self, *args, **kwargs):
		SequentialBackoffTagger.__init__(self, *args, **kwargs)
		self.name_set = set([n.lower() for n in names.words()])
	
	def choose_tag(self, tokens, index, history):
	
		word = tokens[index]
		
		if word is None :
			return None
		
		if word.lower() in self.name_set:
			return 'NP'
		else:
			return None

class COCATagger(SequentialBackoffTagger):
	def __init__(self, *args, **kwargs):
		SequentialBackoffTagger.__init__(self, *args, **kwargs)
		coca_list = csv.reader(open('../files/coca_500k.csv'), delimiter='	')
		self.tag_map = dict()
		for row in coca_list:
			freq = int(row[0])
			word = row[1]
			pos  = row[2]
			self.insertPair(word, pos, freq)
			
		self.tag_converter = TagsetConverter()
	
	def insertPair(self, word, pos, freq):
		""" Appends a (pos,freq) tuple in the end of the list
		corresponding to a word. Since they're ranked in coca file
		it should result in an ordered list by frequency """
		map_ = self.tag_map
		if ( word not in map_):	map_[word] = [(pos, freq)]
		else: map_[word].append((pos,freq))
			
			
	def choose_tag(self, tokens, index, history):
		word = tokens[index]
		if word in self.tag_map: 
			posfreq = self.tag_map[word][0]
			return self.tag_converter.claws7ToBrown(posfreq[0])
		else:
			return None
	
	def getFrequency(self, word, tag):
		pos_freq_pairs = self.tag_map[word]
		for pair in pos_freq_pairs:
			if len(tag)==1:
				pos = self.tag_converter.brownToWordNet(pair[0])
			else:
				pos = pair[0]
			if (pos==tag):
				return pair[1]
		return None
				
				
class SentiWordnetTagger():
	def __init__(self):
		f = '../files/SentiWordNet_3.0.0_20120206.txt'
		self.swn = SentiWordNetCorpusReader(f)
	
	def tag(self, word, pos):
		if (pos is None):
			return (None, 'z')
		synsets = self.swn.senti_synsets(word, pos)
		
		if not synsets: return None
		
		#assumes the list is ranked and gets the first as the most frequent
		s = synsets[0] 
		offset = s.offset
		if s.pos_score > s.neg_score:	 tag = 'p'
		elif  s.pos_score < s.neg_score: tag = 'n'
		else:							 tag = 'z'
		
		# offset is the synset id
		return (offset, tag)

class SemanticTagger():
	
	def __init__(self):
		self.stemmer = PorterStemmer()
		self.names_tagger = NamesTagger()
		self.months = self.getMonthsList()
		self.nationalities = self.getNationalitiesList()
		self.categories = (	
			(self.synsets('animal'), 'animal'),
			(self.synsets('food','fruit'), 'food'),
			(self.synsets('sexual_activity', 'sexy', 'sleep_together', 'kiss'), 'sexual'),
			(self.synsets('feeling','love'), 'feeling'),
			(self.synsets('conflict','aggression'), 'aggression'),
			(self.synsets('color'), 'color'),
			(self.synsets('place'), 'place'),
			(self.synsets('professional'), 'profession'),
			(self.synsets('belief', 'religious_person'), 'religious' ),
			(self.synsets('nation', 'inhabitant'), 'nation' ),
			(self.synsets('body_part'), 'body' ),
			(self.synsets('time_period'), 'time' ),
			(self.synsets('clothing'), 'clothing' ),
			(self.synsets('sports'), 'sports' ),
			(self.synsets('weapon'), 'weapon' ),
			(self.synsets('music'), 'music' ),
			(self.synsets('art'), 'art' ),
			(self.synsets('diversion', 'entertainer'), 'entertainment' ),
			(self.synsets('crime'), 'crime'),
			(self.synsets('person'), 'person' )
			)
	
	def getNationalitiesList(self):
		reader = csv.reader(open('../files/wordlists/nationalities.txt'))
		return [self.stemmer.stem(row[0]).lower() for row in reader]
	
	def getMonthsList(self):
		reader = csv.reader(open('../files/wordlists/months.txt'))
		return [row[0] for row in reader]
	
	def synsets(self, *args):
		a = set()
		for s in args:
			a |= set(wn.synsets(s))
		return a
	
	def _tagIt(self, s):
		paths = s.hypernym_paths()
		for p in paths:
			for cat in self.categories:
				if set(p).intersection(cat[0]):
					return cat[1]
		return None
	
	''' Receives (word, pos [, offset]]). 
	If offset is passed, assumes the meaning associated with the pos in wordnet.
	If just pos is passed, assumes that there's no synset associated with word in wordnet
	and tags according to some rules based on pronouns, proper nouns, etc. '''
	def tag(self, *args):
		word = args[0]
		if word is None :
			return None
		word = word.lower() # lowercasing word
		if (len(args)==3):
			# try to find a match in the synsets bag (wordnet)
			t = self.tag_by_synset(args[1], args[2])
			# if wordnet approach wasn't successful we look for matches in wordlists
			if (t is None):
				t = self.tag_by_wordlist(word, args[1])
		else:
			t = self.tag_by_wordlist(word, args[1])
		
		return t

	
	def tag_by_synset(self, pos, offset):
		if not (pos and offset): return None
		
		s = wn._synset_from_pos_and_offset(pos, offset)
		
		# outputtin verb's paths
		if pos == 'v':
			print s.hypernym_paths()
		
		return self._tagIt(s);
		
	
	''' Receives a word and a tag from Brown tagset.
	Decides about the category independently of Wordnet.
	This function is useful for tagging words whose pos
	couldn't be converted to wordnet, like PP and NP; or which
	simply are not found in wordnet. '''
	def tag_by_wordlist(self, word, pos):
		if pos[:2]=='PP' and pos[2]!='$' and word!='it': 
			return 'person'
		elif pos=='NP' or pos=='NNP' : # named-entity
			if (self.names_tagger.tag([word])[0][1] is not None):
				return 'name'
			elif (word in self.months):
				return 'time'
		elif pos=='JJ' or pos=='a':
			if (self.stemmer.stem(word) in self.nationalities):
				return 'nation'
			
		return None
