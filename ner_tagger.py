import os
import re
from data_wrapper import WrapperTools
import editdistance
from nltk.corpus import words as lexicon

class NER_Tagger:
	"""A simple NER tagger"""

	def train(self,training_file):
		"""Trains a CRF tagger using Mallet"""
		wt = WrapperTools()
 		words = wt.unwrap(training_file)
 		self.featurize(words,"featurized_training")
 		os.system("java -cp " +\
 			"\"../mallet-2.0.8RC3/class:../mallet-2.0.8RC3/lib/mallet-deps.jar\" " +\
 			"cc.mallet.fst.SimpleTagger --train true " +\
 			"--model-file trained_model featurized_training")


	def test(self,test_file):
		"""Tests the trained tagger using Mallet"""
		wt = WrapperTools()
 		words = wt.unwrap(test_file)
 		self.featurize(words,"featurized_test",False)
 		os.system("java -cp " +\
 			"\"../mallet-2.0.8RC3/class:../mallet-2.0.8RC3/lib/mallet-deps.jar\" " +\
 			"cc.mallet.fst.SimpleTagger " +\
 			"--model-file trained_model featurized_test > tagged_test" )
 		#self.post_process("tagged_test", words)
 		#print self.get_precision_and_recall(words,"tagged_test_postprocessed")
 		print self.get_precision_and_recall(words,"tagged_test")


 	def post_process(self, tags_file, test_tweets):
 		with open(tags_file) as tagfile:
 			tags = [line.strip() for line in tagfile.readlines()]
 		
 		test_words = []
 		for tweet in test_tweets:
 			for entry in tweet:
 				test_words.append(entry[-2])
 			test_words.append('')

 		new_tags = []
 		for i in range(len(test_words)):
 			if test_words[i].startswith('#') or test_words[i].startswith('@') or test_words[i].startswith('http') and tags[i] != 'O':
 				new_tags.append('O')
 			else:
 				new_tags.append(tags[i])
 		# new_tags = [tags[0]]
 		# for i in range(1,len(tags)):
 		# 	if tags[i-1] == 'O' and tags[i] == 'I':
 		# 		new_tags.append('B')
 		# 	else:
 		# 		new_tags.append(tags[i])
 		with open("tagged_test_postprocessed", 'w') as newtagfile:
 			newtagfile.write('\n'.join(new_tags))

 	def get_precision_and_recall(self,tweets,test):
 		"""Compares the gold standard with the tagged file
 		returns precision, recall"""
 		tp = 0
 		fp = 0
 		tn = 0
 		fn = 0
 		total = 0
 		t = open(test)
 		g = [word for words in tweets for word in words]
 		for line in t:
 			new = line.strip()
 			if len(new) == 0:
 				continue
 			gold = g[total][-1]
 			if gold == "O":
 				if new == "O":
 					tn += 1
 				else:
 					fp += 1
 					#print total, new, g[total][-1], g[total][-2]
 			else:
 				if new == gold:
 					tp += 1
 				else:
 					fn += 1
 					print total, new, g[total][-1], g[total][-2]#, g[total][:-2]
 			total += 1
 		print tp, tn, fp, fn, total
 		p = float(tp)/float(tp+fp)
 		r = float(tp)/float(tp+fn)
 		f1 = 2*p*r/(p+r)
 		return p,r,f1


	def featurize(self,tweets,output="featurized",label=True):
		"""Takes the output of WrapperTools and creates a document
		in the necessary format for Mallet, i.e. 
		f1 f2 ... fn label"""
		fw = open(output,"w")
		# Put featurizing methods here; if they are all in the output format 
		# [[f1, f2, word, tag]...], just appending each new feature to the beginning
		# of the list, it should be easy to write to the file and keep all features separate
		# Inefficient, but easier to keep straight when all of us 
		# work on separate features

		#names_dict is only retrieved once to increase efficiency
		names_dict = self.read_names("census_first_names", {})
		names_dict = self.read_names("census_last_names", names_dict)
		cities_dict = self.read_cities("us_cities", {})
		word_dict = set(lexicon.words())

		tweets = self.starts_with_punctuation(tweets)
		tweets = self.is_word_shape_like_ne(tweets)
		tweets = self.is_a_name(tweets, names_dict, word_dict)
		tweets = self.whole_tweet_is_upper_lower(tweets)
		tweets = self.word_begins_with_capital(tweets)
		# tweets = self.prev_next_BIO_tag(tweets)
		tweets = cluster_features(tweets)
		tweets = dictionary_features(tweets)
		tweets = token_context(tweets)
		tweets = pos_tag(tweets)
		tweets = self.is_a_city(cities_dict, tweets)
		#tweets = self.is_word_misspelled(tweets, word_dict)

		for tweet in tweets:
			for word in tweet:
				for i in range(len(word)):
					if i < len(word)-1 or label:
						fw.write(str(word[i])+" ")
				fw.write("\n")
			fw.write("\n")
		fw.close()
		return

	def is_a_name(self, tweets, names_dict, word_dict):
		"""
			Checks for names in the tweets
		"""
		print len(word_dict)
		for tweet in tweets:
			for word in tweet:
				entity = word[-2].lower()
				if entity in names_dict:
					if entity not in word_dict:
						word.insert(0, "is_name")
					else:
						word.insert(0,"might_be_name") # Differentiate between words that are definitely names and not?
				else:
					word.insert(0, "is_not_a_name")
		return tweets


	def read_names(self, filename, names_dict):
		""" 
			Retrieves names fron census bureau files
		"""
		the_file = open(filename)
		all_lines = the_file.readlines()
		# line.split()[0] is the name itself
		# hashing allows of O(1) checks. The 1 is meaningless
		for line in all_lines:
			names_dict[line.split()[0].lower()] = 1
		return names_dict


	def whole_tweet_is_upper_lower(self, tweets):
		"""
			Checks to see if the whole tweet is in one case
		"""
		for tweet in tweets:
			boolean = self.individual_tweet_is_upper_lower(tweet)
			# apply feature to each word in tweet
			for word in tweet:
				if boolean:
					word.insert(0, "is_one_case")
				else:
					word.insert(0, "is_not_one_case")
		return tweets


	def individual_tweet_is_upper_lower(self, tweet):
		"""
			Helper method for whole_tweet_is_upper_lower
		"""
		lower = [1 for word in tweet if word[-2].islower()]
		upper = [1 for word in tweet if word[-2].isupper()]
		return len(upper) == len(tweet) or len(lower) == len(tweet)


	def word_begins_with_capital(self, tweets):
		"""
			Checks if word begins with a capital letter
		"""
		for tweet in tweets:
			for word in tweet:
				if word[-2][0].isupper():
					word.insert(0, "begins_with_capital")
				else:
					word.insert(0, "doesnt_begin_with_capital")
		return tweets


	def prev_next_BIO_tag(self, tweets):
		"""
			Checks the BIO tag of the previous and next words
		"""
		for tweet in tweets:
			for word_index, word in enumerate(tweet):
				if word_index != 0:
					word.insert(0, "prev_tag_"+str(tweet[word_index-1][-1]))
				if word_index != len(tweet)-1:
					word.insert(0, "next_tag_"+str(tweet[word_index+1][-1]))
		return tweets

	def is_a_city(self, cities_dict, tweets):
		"""
			Checks for city names in the tweets
		"""
		for tweet in tweets:
			for word in tweet:
				if word[-2].lower() in cities_dict:
					word.insert(0, "is_city")
		return tweets		

	def read_cities(self, filename, cities_dict):
		"""
			Retrieves city names from list of cities in the US
		"""
		the_file = open(filename)
		all_lines = the_file.readlines()
		# hashing allows of O(1) checks. The 1 is meaningless
		for line in all_lines:
			cities_dict[line.lower()] = 1
		return cities_dict

	def read_cities(self, filename, cities_dict):
		"""
			Retrieves city names from list of cities in the US
		"""
		the_file = open(filename)
		all_lines = the_file.readlines()
		# hashing allows of O(1) checks. The 1 is meaningless
		for line in all_lines:
			cities_dict[line.lower()] = 1
		return cities_dict


	def starts_with_punctuation(self, tweets):
		for tweet in tweets:
			i = 0
			for entry in tweet:
				word = entry[-2]
				if word.startswith("@") or word.startswith("#") or len(word) < 2:
					entry.insert(0,"starts_with_punc")
				elif word.find("http") > -1 or re.search(r"\.[a-z]{3}",word):
					entry.insert(0,"starts_with_punc")
				elif re.match("[0-9]+",word):
					entry.insert(0,"is_number")
				i+=1
		return tweets

	def is_word_shape_like_ne(self, tweets):
		"""Adds a feature for whether the word shape is likely to be 
		a named entity, checking that the previous word is not EOS,
		and other punctuation"""
		capsword = re.compile(r"[A-Z][a-z]+")
		punc = re.compile(r"[.!?:]")
		caps_non_entities = self.load_set_from_file("capitalized_non_entities.txt")
		for tweet in tweets:
			i = 0
			for entry in tweet:
				word = entry[-2]
				if word.lower() in caps_non_entities:
					entry.insert(0,"is_capitalized_not_ne")
				elif re.match(capsword,word) and i != 0 and not re.match(punc,tweet[i-1][-2]):
						entry.insert(0,"is_caps")
				i+=1
		return tweets

	def is_word_misspelled(self, tweets, word_dict):
		"""Adds a feature for whether the word is likely to be a word that 
		is commonly misspelled, so that we can differentiate words not in the dictionary
		that might be proper nouns from misspellings"""
		common_misspellings = self.load_set_from_file("common_spelling_errors.txt")
		for tweet in tweets:
			i = 0
			for entry in tweet:
				word = entry[-2].lower()
				if word not in word_dict:
					not_misspelling = True
					for cm in common_misspellings:
						if editdistance.eval(word,cm) < 3: 
							entry.insert(0,"is_misspelling")
							not_misspelling = False
							break
					if not_misspelling:
						entry.insert(0,"misspelling_or_proper")
				else:
					entry.insert(0,"in_dictionary")
				i+=1
		return tweets


	def load_set_from_file(self, filename):
		newset = set()
		f = open(filename)
		for line in f:
			newset.add(line.strip().lower())
		return newset


def brown2bits(bits):
	"""function credit: Twitter NLP
	converts brown number to bitstring"""
	bitstring = ""
	for i in range(20):
	    if int(bits) & (1 << i):
	        bitstring += '1'
	    else:
	        bitstring += '0'
	return str(bitstring)

def read_clusters():
	clusterdict = {}
	with open('../twitter_nlp/data/brown_clusters/60K_clusters.txt') as clusterfile:
		for line in clusterfile.readlines():
			lineList = line.split()
			clusterdict[lineList[0]] = brown2bits(lineList[1])
	return clusterdict

def read_dictionary(fpath):
	with open(fpath) as dictfile:
		dictlist = [line.lower().strip() for line in dictfile.readlines()]
	return set(dictlist)

def cluster_features(tweets):
	"""get brown cluster prefixes for the corpus"""
	clusterdict = read_clusters()
	for tweet in tweets:
		for i in range(len(tweet)):
			token = tweet[i][-2].lower()
			if token in clusterdict:
				cluster = clusterdict[token]
				tweet[i].insert(0, 'cluster'+cluster[:4])
				# tweet[i].insert(0, 'cluster'+cluster[:8])
				# tweet[i].insert(0, 'cluster'+cluster[:12])
				#word.insert(0, 'cluster'+cluster[:4])
				#word.insert(0, 'cluster'+cluster[:8])
				#word.insert(0, 'cluster'+cluster[:12])
				if i != 0:
					prevtoken = tweet[i-1][-2].lower()
					if prevtoken in clusterdict:
						prevcluster = clusterdict[prevtoken]
						tweet[i].insert(0, 'prevcluster'+prevcluster[:4])
				if i != (len(tweet)-1):
					nexttoken = tweet[i+1][-2].lower()
					if nexttoken in clusterdict:
						nextcluster = clusterdict[nexttoken]
						tweet[i].insert(0, 'nextcluster'+nextcluster[:4])
	return tweets

def dictionary_features(tweets):
	dict_main_path = '../twitter_nlp/data/dictionaries/'
	auto_make = read_dictionary(dict_main_path+'automotive.make')
	auto_model = read_dictionary(dict_main_path+'automotive.model')
	events = read_dictionary(dict_main_path+'base.events.festival_series')
	book_paper = read_dictionary(dict_main_path+'book.newspaper')
	channel = read_dictionary(dict_main_path+'broadcast.tv_channel')
	brand = read_dictionary(dict_main_path+'business.brand')
	company = read_dictionary(dict_main_path+'business.consumer_company')
	consumer_product = read_dictionary(dict_main_path+'business.consumer_company')
	sponsor = read_dictionary(dict_main_path+'business.sponsor')
	uni = read_dictionary(dict_main_path+'education.university')
	stop = read_dictionary(dict_main_path+'english.stop')
	gov = read_dictionary(dict_main_path+'government.government_agency')
	loc = read_dictionary(dict_main_path+'location')
	website = read_dictionary(dict_main_path+'internet.website')
	country = read_dictionary(dict_main_path+'location.country')
	product = read_dictionary(dict_main_path+'product')
	league = read_dictionary(dict_main_path+'sports.sports_league')
	team = read_dictionary(dict_main_path+'sports.sports_team')
	holiday = read_dictionary(dict_main_path+'time.holiday')
	recurring_event = read_dictionary(dict_main_path+'time.recurring_event')
	road = read_dictionary(dict_main_path+'transportation.road')
	network = read_dictionary(dict_main_path+'tv.tv_network')
	program = read_dictionary(dict_main_path+'tv.tv_program')
	vc_comp = read_dictionary(dict_main_path+'venture_capital.venture_funded_company')
	venue = read_dictionary(dict_main_path+'venues')
	lower100 = read_dictionary(dict_main_path+'lower.100')
	lower500 = read_dictionary(dict_main_path+'lower.500')
	lower1000 = read_dictionary(dict_main_path+'lower.1000')
	lower5000 = read_dictionary(dict_main_path+'lower.5000')
	lower10000 = read_dictionary(dict_main_path+'lower.10000')

	for tweet in tweets:
		for word in tweet:
			token = word[-2].lower()
			if token in auto_make:
				word.insert(0, 'auto_make')
			if token in auto_model:
				word.insert(0, 'auto_model')
			if token in events:
				word.insert(0, 'events')
			if token in book_paper:
				word.insert(0, 'book_paper')
			if token in channel:
				word.insert(0, 'channel')
			if token in brand:
				word.insert(0, 'brand')
			if token in company:
				word.insert(0, 'company')
			if token in consumer_product:
				word.insert(0, 'consumer_product')
			if token in sponsor:
				word.insert(0, 'sponsor')
			if token in uni:
				word.insert(0, 'uni')
			if token in stop:
				word.insert(0, 'stop')
			if token in gov:
				word.insert(0, 'gov')
			if token in loc:
				word.insert(0, 'loc')
			if token in website:
				word.insert(0, 'website')
			if token in country:
				word.insert(0, 'country')
			if token in product:
				word.insert(0, 'product')
			if token in league:
				word.insert(0, 'league')
			if token in team:
				word.insert(0, 'team')
			if token in holiday:
				word.insert(0, 'holiday')
			if token in recurring_event:
				word.insert(0, 'recurring_event')
			if token in road:
				word.insert(0, 'road')
			if token in network:
				word.insert(0, 'network')
			if token in program:
				word.insert(0, 'program')
			if token in vc_comp:
				word.insert(0, 'vc_comp')
			if token in venue:
				word.insert(0, 'venue')
			if token in lower100:
				word.insert(0, 'lower100')
			if token in lower500:
				word.insert(0, 'lower500')
			if token in lower1000:
				word.insert(0, 'lower1000')
			if token in lower5000:
				word.insert(0, 'lower5000')
			if token in lower10000:
				word.insert(0, 'lower10000')
	return tweets

def token_context(tweets):
	"""get two previous and two next tokens"""
	for tweet in tweets:
		for i in range(len(tweet)):
			if i != 0:
				prev_token = tweet[i-1][-2]
				tweet[i].insert(0, 'prev_token:'+prev_token)
			if i != (len(tweet)-1):
				next_token = tweet[i+1][-2]
				tweet[i].insert(0, 'next_token:'+next_token)
			if i > 1:
				prevprev_token = tweet[i-2][-2]
				tweet[i].insert(0, 'prevprev_token:'+prevprev_token)
			if i < (len(tweet)-2):
				nextnext_token = tweet[i+2][-2]
				tweet[i].insert(0, 'nextnext_token:'+nextnext_token)
			#tweet[i].insert(0, 'token:'+tweet[i][-2])
	return tweets

def pos_tag(tweets):
	#create input file
	os.chdir('twitie-tagger')
	with open('pos_input', 'w') as infile:
		tokens = []
		for tweet in tweets:
			for entry in tweet:
				tokens.append(entry[-2])
		infile.write('\n'.join(tokens))
	os.system('java -jar twitie_tag.jar models/gate-EN-twitter.model pos_input > pos_output')

	with open('pos_output', 'r') as outfile:
		pos_tags = []
		for line in outfile.readlines():
			pos_tags.append(line.split('_')[-1].strip())

	word_ind = 0
	for tweet in tweets:
		for i in range(len(tweet)):
			tweet[i].insert(0, 'curr_pos'+pos_tags[word_ind])
			if i != 0:
				tweet[i].insert(0, 'prev_pos:'+pos_tags[word_ind-1])
			if i > 1:
				tweet[i].insert(0, 'prevprev_pos:'+pos_tags[word_ind-2])

			if i != (len(tweet)-1):
				tweet[i].insert(0, 'next_pos:'+pos_tags[word_ind+1])

			# if i < (len(tweet)-2):
			# 	tweet[i].insert(0, 'nextnext_pos:'+pos_tags[word_ind+2])
			word_ind += 1
	os.chdir('..')

	return tweets			

if __name__ == "__main__":
	wt = WrapperTools()
 	words = wt.unwrap("./proj1-data/train.gold")
 	NT = NER_Tagger()
 	NT.train("./proj1-data/train.gold")
 	NT.test("./proj1-data/dev.gold")
 	NT.test("./proj1-data/test.gold")