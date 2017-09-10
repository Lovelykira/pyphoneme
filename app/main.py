from phoneme_parser import TextSynthesis

SENTENCE = 'sentence'
WORD = 'word'


if __name__ == '__main__':
    file = open("file.txt", "r")
    text = file.read()
    # TextSynthesis(text=text, mode=SENTENCE).synthesize_by_deleting_chunks()
    TextSynthesis(text=text, mode=SENTENCE).synthesize_by_appending_chunks()
