from export import SpreadsheetExport
from phoneme_parser import TextSynthesis


if __name__ == '__main__':
    file = open('app/Airport-Arthur_Hailey.txt', "r")
    text = file.read()

    PARAMETERS = [
        # {'text': text, 'mode': 'word', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'append', 'phoneme_group_size': 1},
        # {'text': text, 'mode': 'word', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'append', 'phoneme_group_size': 2},
        # {'text': text, 'mode': 'word', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'append', 'phoneme_group_size': 3},

        {'text': text, 'mode': 'word', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'delete', 'phoneme_group_size': 1},
        #{'text': text, 'mode': 'word', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'delete', 'phoneme_group_size': 2},
        #{'text': text, 'mode': 'word', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'delete', 'phoneme_group_size': 3},

        # {'text': text, 'mode': 'word', 'distribution_criteria': 'statistic', 'synthesis_mode': 'append', 'phoneme_group_size': 1},
        #{'text': text, 'mode': 'word', 'distribution_criteria': 'statistic', 'synthesis_mode': 'append', 'phoneme_group_size': 2},
        #{'text': text, 'mode': 'word', 'distribution_criteria': 'statistic', 'synthesis_mode': 'append', 'phoneme_group_size': 3},

        # {'text': text, 'mode': 'word', 'distribution_criteria': 'statistic', 'synthesis_mode': 'delete', 'phoneme_group_size': 1},
        #{'text': text, 'mode': 'word', 'distribution_criteria': 'statistic', 'synthesis_mode': 'delete', 'phoneme_group_size': 2},
        #{'text': text, 'mode': 'word', 'distribution_criteria': 'statistic', 'synthesis_mode': 'delete', 'phoneme_group_size': 3},


        # {'text': text, 'mode': 'sentence', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'append', 'phoneme_group_size': 1},
        # {'text': text, 'mode': 'sentence', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'append', 'phoneme_group_size': 2},
        #{'text': text, 'mode': 'sentence', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'append', 'phoneme_group_size': 3},

        # {'text': text, 'mode': 'sentence', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'delete', 'phoneme_group_size': 1},
        #{'text': text, 'mode': 'sentence', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'delete', 'phoneme_group_size': 2},
        #{'text': text, 'mode': 'sentence', 'distribution_criteria': 'pvalue', 'synthesis_mode': 'delete', 'phoneme_group_size': 3},

        # {'text': text, 'mode': 'sentence', 'distribution_criteria': 'statistic', 'synthesis_mode': 'append', 'phoneme_group_size': 1},
        #{'text': text, 'mode': 'sentence', 'distribution_criteria': 'statistic', 'synthesis_mode': 'append', 'phoneme_group_size': 2},
        #{'text': text, 'mode': 'sentence', 'distribution_criteria': 'statistic', 'synthesis_mode': 'append', 'phoneme_group_size': 3},

        # {'text': text, 'mode': 'sentence', 'distribution_criteria': 'statistic', 'synthesis_mode': 'delete', 'phoneme_group_size': 1},
        #{'text': text, 'mode': 'sentence', 'distribution_criteria': 'statistic', 'synthesis_mode': 'delete', 'phoneme_group_size': 2},
        #{'text': text, 'mode': 'sentence', 'distribution_criteria': 'statistic', 'synthesis_mode': 'delete', 'phoneme_group_size': 3},
    ]

    for params in PARAMETERS:
        text_synth = TextSynthesis(**params)

        text_synth.synthesis()
        SpreadsheetExport(data=text_synth.get_results()).save()
