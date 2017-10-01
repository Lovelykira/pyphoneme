from subprocess import check_output
from nltk.tokenize import RegexpTokenizer


def main():


	tokenizer = RegexpTokenizer(r'\w+')

	data=[]
	with open('../data/string.txt', 'r') as myfile:
	    content=myfile.read().replace('\n', ' ')
	myfile.close()



	chunk_size=10
	data = tokenizer.tokenize(content)
	for iWord in xrange(0,chunk_size):
		data.append('')

	transcriptions=[]
	for iWord in xrange(0,len(data),chunk_size):
		se=' '.join(data[iWord:iWord+chunk_size])
		tr=check_output(["espeak", "-q", "--ipa", '-v', 'en-us', se]).decode('utf-8')
		print(se, ' ', tr)
		letters=[item for item in tr]
		print('-'.join(letters))
		#return
		transcriptions.append(tr)

	#print(transcriptions)

if __name__ == '__main__':
	main()
