import os
from data_wrapper import WrapperTools

class NER_Tagger:
	"""A simple NER tagger"""

	def train(self,training_file):
		"""Trains a CRF tagger using Mallet"""
		wt = WrapperTools()
 		words = wt.unwrap(training_file)
 		self.featurize(words)
 		os.system("java -cp " +\
 			"\"../mallet-2.0.8RC3/class:../mallet-2.0.8RC3/lib/mallet-deps.jar\" " +\
 			"cc.mallet.fst.SimpleTagger --train true " +\
 			"--model-file trained_model " + feature_doc)


	def test(self,test_file):
		"""Tests the trained tagger using Mallet"""
		wt = WrapperTools()
 		words = wt.unwrap(test_file)
 		self.featurize(words)
 		os.system("java -cp " +\
 			"\"../mallet-2.0.8RC3/class:../mallet-2.0.8RC3/lib/mallet-deps.jar\" " +\
 			"cc.mallet.fst.SimpleTagger " +\
 			"--model-file trained_model " + test_file)


	def featurize(self,words):
		"""Takes the output of WrapperTools and creates a document
		in the necessary format for Mallet, i.e. 
		f1 f2 ... fn label"""
		fw = open("featurized","w")
		# Put featurizing methods here; if they are all in the output format 
		# [(f1, f2, word, tag)...], just appending each new feature to the beginning
		# of the list, it should be easy to write to the file and keep all features separate
		# Inefficient, but easier to keep straight when all of us 
		# work on separate features

		#names_dict is only retrieved once to increase efficiency
		names_dict = self.read_names("census_first_names", {})
		names_dict = self.read_names("census_last_names", names_dict)

		for tweet in tweets:
			for word in tweet:

				### FEATURE FUNCTIONS ###

				# word is a name
				word.append(self.features_is_a_name(word[0]), names_dict)


				### END FEATURE FUNCTIONS ###

				fw.write(w)
		fw.close()
		return


	def feature_is_a_name(self, word, names_dict):
		return word.lower() in names_dict


	def read_names(self, filename, names_dict):
		""" 
			Retrieves names fron census bureau files
		"""
		the_file = open(filepath)
		all_lines = the_file.readlines()
        # line.split()[0] is the name itself
        # hashing allows of O(1) checks. The 1 is meaningless
		for line in all_lines:
			names_dict[line.split()[0].lower()] = 1
		return names_dict
