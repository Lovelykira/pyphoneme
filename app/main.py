from phoneme_parser import TextSynthesis
from export import SpreadsheetExport

SENTENCE = 'sentence'
WORD = 'word'


if __name__ == '__main__':
    file = open("file.txt", "r")
    text = file.read()
    text_synth = TextSynthesis(text=text, mode=SENTENCE)
    text_synth.synthesize_by_appending_chunks()
    # TextSynthesis(text=text, mode=WORD).synthesize_by_appending_chunks()
    SpreadsheetExport(data=text_synth.get_results()).save()
