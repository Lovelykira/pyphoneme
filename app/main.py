from phoneme_parser import TextSynthesis
from export import SpreadsheetExport
import argparse

SENTENCE = 'sentence'
WORD = 'word'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Text synthesis')
    parser.add_argument('--mode', dest='mode', default='sentence', help='Sets paring mode (word or sentence). Default: sentence')
    parser.add_argument('--compare', dest='compare', default='pvalue', help='Sets compare method (pvalue or statistics). Default: pvalue')
    parser.add_argument('--pvalue', type=float, dest='pvalue', default=0.7, help='Sets pvalue. Default: 0.7')
    parser.add_argument('--method', dest='method', default='append', help='Sets synthes method (append or delete). Default: append')
    parser.add_argument('--file', dest='file', default='file.txt', help='Sets file to read from initial text. Default: file.txt')
    parser.add_argument('--report', dest='report', default='true', help='If report should be generated. Default: true')

    args = parser.parse_args()
    mode = WORD if args.mode == 'word' else SENTENCE
    compare = TextSynthesis.PVALUE if args.compare == 'pvalue' else TextSynthesis.STATISTIC

    file = open(args.file, "r")

    text = file.read()
    text_synth = TextSynthesis(text=text, mode=mode, p_value_level=args.pvalue, distribution_criteria=compare, synthesis_mode=args.method)

    text_synth.synthesis()

    if args.report not in ['false', 'no', 'skip', 0]:
        SpreadsheetExport(data=text_synth.get_results()).save()
