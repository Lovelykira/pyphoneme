import datetime
import json
import re
import requests
from bs4 import BeautifulSoup
from scipy import stats


class PhonemeParser:
    """
    Class that gets transcription for given text.
    """
    AVAILABLE_LANGUAGES = ('english', 'danish', 'german')
    DEFAULT_LANGUAGE = 'english'
    ALPHABET = 'IPA'
    URL2 = 'http://upodn.com/phon.php'
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'

    def __init__(self, language=None):
        self.language = language if language in self.AVAILABLE_LANGUAGES else self.DEFAULT_LANGUAGE

    def text_to_phoneme(self, text):
        """
        Gets text and returns it's transcription. Only first 500 words will get translations.
        :param text: string
        :return: string, transcription
        """
        html_doc = self._get_html(text)
        soup = BeautifulSoup(html_doc, 'html.parser')
        return soup.find_all('td')[1].find('font').text.strip()

    def _get_html(self, text):
        request = {'intext': text, 'ipa': 0}
        headers = {'User-Agent': self.USER_AGENT}
        s = requests.Session()
        res = s.post(self.URL2, request, headers=headers)
        return res.text


def remove_dots(text):
    return text.replace('.', ' ').strip()


def remove_empty_values(words):
    return list(filter(lambda a: a != '', words))


def get_normalized_word(word):
    """
    Gets word and removes all non letter symbols from it
    :param word: string
    :return: string, containing only letters
    """
    return re.sub('[^a-zA-Z]', '', word)


class SavedPhonemeWords:
    """
    Class that saves/gets words and theirs phonemes to/from file.
    """
    FILE_NAME = "saved_phonemes.json"

    @classmethod
    def get(cls):
        """
        opens file and gets from it words and their phonemes
        :return: dict {'word': 'phoneme'} or an empty dict
        """
        try:
            words_file = open(cls.FILE_NAME, "r")
            read = words_file.read()
            saved_phoneme_words = json.loads(read)
            words_file.close()
        except:
            saved_phoneme_words = dict()
        return saved_phoneme_words

    @classmethod
    def update(cls, saved_phoneme_words):
        """
        opens file and saves dict
        :param saved_phoneme_words: dict to be saved
        """
        file = open(cls.FILE_NAME, "w")
        file.write(json.dumps(saved_phoneme_words))
        file.close()


class UniquePhonemeWords:
    """
    Class that gets unique words and their phonemes from text.
    """
    def __init__(self, text):
        self.text = text
        self.words = [get_normalized_word(word) for word in text.split(' ') if word]

    def get(self):
        """
        Returns unique words and their phonemes from text. The method looks at SavedPhonemeWords first, to minimize
        number of requests.
        :return:
        """
        saved_phoneme_words = SavedPhonemeWords.get()
        current_text_phoneme_words = dict()
        for word in self.words:
            if word in current_text_phoneme_words.keys():
                continue
            if word not in saved_phoneme_words.keys():
                try:
                    phoneme = PhonemeParser().text_to_phoneme(word)
                except:
                    SavedPhonemeWords.update(saved_phoneme_words)
                saved_phoneme_words[word] = phoneme
                print('Getting phoneme for ' + word + ' - ' + phoneme)
            current_text_phoneme_words[word] = saved_phoneme_words[word]

        SavedPhonemeWords.update(saved_phoneme_words)
        return current_text_phoneme_words


class TextAnalyzer:
    """
    Class to analyze text
    """
    def __init__(self, text):
        self.text = text
        self.words_info = {}
        self.phonemes_count = {}
        self.all_phonemes = 0

        self.unique_phoneme_words = UniquePhonemeWords(self.text).get()
        print('unique phonemes found')

        self._analyze_words()
        self._analyze_phonemes()

    def _get_words_list(self):
        text = [get_normalized_word(word) for word in self.text.split(' ')]
        return remove_empty_values(text)

    def _analyze_words(self):
        """
        Loops thought all words and saves information to self.words_info.
        """
        words = self._get_words_list()

        for current_word in words:
            if current_word in self.words_info:
                self.words_info[current_word]['count'] += 1
            else:
                transcription = self.unique_phoneme_words[current_word]
                self.words_info[current_word] = {
                    'count': 1,
                    'word': Word(current_word, transcription)
                }

    def _analyze_phonemes(self):
        """
        Loops through all phonemes and saves how much of each phonemes there are and sum of all phonemes in text.
        """
        for word_text, word_info in self.words_info.items():
            for phoneme, phoneme_count in word_info['word'].get_phonemes_count().items():
                self.all_phonemes += phoneme_count * word_info['count']
                self.phonemes_count[phoneme] = self.phonemes_count.get(phoneme, 0) + phoneme_count * word_info['count']

    def get_initial_percentage(self):
        """
        Calculates how much percentage does each phoneme take in initial text.
        :return: dict {phoneme: percentage}
        """
        percentage = {}
        for phoneme, count in self.phonemes_count.items():
            percentage[phoneme] = count / self.all_phonemes
        return percentage

    def get_percentage(self, chunk):
        """
        Calculates how much percentage does each phoneme take in given chunk of initial text.
        :param chunk: string, part of initial text
        :return: dict {phoneme: percentage}
        """
        all_phonemes = 0
        phonemes = {}
        for word in chunk.split(' '):
            word = get_normalized_word(word)
            if not word:
                continue
            phonemes_count = self.words_info[word]['word'].get_phonemes_count()
            for phoneme, count in phonemes_count.items():
                phonemes[phoneme] = phonemes.get(phoneme, 0) + count
                all_phonemes += count

        percentage = {}
        for phoneme, count in phonemes.items():
            percentage[phoneme] = count / all_phonemes
        return percentage


class TextSynthesis:
    """
    Class that synthesises new text
    """
    PVALUE = 'pvalue'
    STATISTIC = 'statistic'
    SENTENCE = 'sentence'
    WORD = 'word'
    AVAILABLE_CRETERIAS = [PVALUE, STATISTIC]
    AVAILABLE_MODES = [SENTENCE, WORD]
    DEFAULT_CRETERIA = PVALUE
    DEFAULT_MODE = SENTENCE

    def __init__(self, text, mode=None, p_value_level=0.7, distribution_criteria=None):
        self.text = self._normalize_text(text)
        self.p_value_level = p_value_level
        self.mode = mode if mode in self.AVAILABLE_MODES else self.DEFAULT_MODE
        self.distribution_criteria = distribution_criteria if distribution_criteria in self.AVAILABLE_CRETERIAS else self.DEFAULT_CRETERIA
        self.text_analyzer = TextAnalyzer(self.text)
        self.initial_distribution = self.text_analyzer.get_initial_percentage()
        print('self.initial_distribution', self.initial_distribution)

    def synthesize_by_deleting_chunks(self):
        """
        Synthesizes result text by deleting chunks that are less relevant.
        At every step of te loop, the chunk that has furthest distribution from text's.
        This chunks is removed from text.
        The loop ends when text's distribution is not relevant.
        :return: string, result text
        """
        text_list = self._text_to_list_by_mode()
        chunks = self._get_chunks_by_mode()
        iterations_number = 0
        while_start = datetime.datetime.now()
        while self.text_is_relevant(' '.join(text_list)):
            loop_start = datetime.datetime.now()
            text_distribution = self.text_analyzer.get_percentage(' '.join(text_list))
            worst_chunk = self.get_worst_chunk(chunks, text_distribution)
            chunks = [value for value in chunks if value != worst_chunk]
            text_list = [value for value in text_list if value != worst_chunk]

            iterations_number += 1
            print('iteration', iterations_number)
            print('time', datetime.datetime.now() - loop_start)
            print('removing', worst_chunk)
        print('whole time', datetime.datetime.now() - while_start)
        print('p_value_level', self.p_value_level)
        print('distribution_criteria', self.distribution_criteria)
        print('mode', self.mode)
        print('result', ' '.join(chunks))
        return ' '.join(chunks)

    def synthesize_by_appending_chunks(self):
        """
        Synthesizes result text by getting most relevant chunk from initial text.
        At every step of the loop, the chunk that has closest distribution to text's is picked.
        This chunk is added to result and removed from text.
        The loop ends when the distribution of result is close to initial distribution
        :return: string, result text
        """
        result_chunks = ''
        text_list = self._text_to_list_by_mode()
        chunks = self._get_chunks_by_mode()
        iterations_number = 0
        while_start = datetime.datetime.now()
        while not self.text_is_relevant(result_chunks):
            loop_start = datetime.datetime.now()
            text_distribution = self.text_analyzer.get_percentage(' '.join(text_list))
            best_chunk = self.get_best_chunk(chunks, text_distribution)
            result_chunks += ' ' + best_chunk + '.'
            chunks = [value for value in chunks if value != best_chunk]
            text_list = [value for value in text_list if value != best_chunk]

            iterations_number += 1
            print('iteration', iterations_number)
            print('time', datetime.datetime.now() - loop_start)
            print('result', best_chunk)
        print('whole time', datetime.datetime.now() - while_start)
        print('p_value_level', self.p_value_level)
        print('distribution_criteria', self.distribution_criteria)
        print('mode', self.mode)
        print('result', result_chunks)
        return result_chunks

    def get_best_chunk(self, chunks, text_distribution):
        """
        Gets most relevant chunk from chunks. Looks at self.distribution_criteria and picks the chunk that is fits best.
        :param chunks: list of chunks
        :param text_distribution: initial distribution to compare
        :return: best chunk, string
        """
        chunks_ks_test = {}
        highest_p_value = -1
        highest_p_value_chunk = None
        smallest_statistic = 2
        smallest_statistic_chunk = None
        for i, chunk in enumerate(chunks):
            if not chunk:
                continue
            chunk_distribution = self.text_analyzer.get_percentage(chunk)
            ks_test = stats.ks_2samp(list(chunk_distribution.values()), list(text_distribution.values()))
            chunks_ks_test[i] = ks_test

            if ks_test.statistic < smallest_statistic:
                smallest_statistic = ks_test.statistic
                smallest_statistic_chunk = chunk
            if ks_test.pvalue > highest_p_value:
                highest_p_value = ks_test.pvalue
                highest_p_value_chunk = chunk

        if self.distribution_criteria == self.PVALUE:
            return highest_p_value_chunk
        if self.distribution_criteria == self.STATISTIC:
            return smallest_statistic_chunk

    def get_worst_chunk(self, chunks, text_distribution):
        """
        Gets least relevant chunk from chunks. Looks at self.distribution_criteria and picks the chunk that is less
        relevant.
        :param chunks: list of chunks
        :param text_distribution: initial distribution to compare
        :return: least relevant chunk, string
        """
        chunks_ks_test = {}
        smallest_p_value = 2
        smallest_p_value_chunk = None
        highest_statistic = -1
        highest_statistic_chunk = None
        for i, chunk in enumerate(chunks):
            if not chunk:
                continue
            chunk_distribution = self.text_analyzer.get_percentage(chunk)
            ks_test = stats.ks_2samp(list(chunk_distribution.values()), list(text_distribution.values()))
            chunks_ks_test[i] = ks_test

            if ks_test.statistic > highest_statistic:
                highest_statistic = ks_test.statistic
                highest_statistic_chunk = chunk
            if ks_test.pvalue < smallest_p_value:
                smallest_p_value = ks_test.pvalue
                smallest_p_value_chunk = chunk

        if self.distribution_criteria == self.PVALUE:
            return smallest_p_value_chunk
        if self.distribution_criteria == self.STATISTIC:
            return highest_statistic_chunk

    def _get_chunks_by_mode(self):
        if self.mode == self.SENTENCE:
            return self.text.split('.')
        if self.mode == self.WORD:
            return self.text_analyzer.unique_phoneme_words.keys()

    def _text_to_list_by_mode(self):
        if self.mode == self.SENTENCE:
            return self.text.split('.')
        if self.mode == self.WORD:
            return [get_normalized_word(word) for word in self.text.split(' ')]

    def text_is_relevant(self, text):
        """
        Compares distributions of given text and initial. Returns whether the text has similar distribution or not.
        :param text: string
        :return: bool
        """
        if not text:
            return False
        synthesis_text_distribution = self.text_analyzer.get_percentage(text)
        ks_test = stats.ks_2samp(list(synthesis_text_distribution.values()), list(self.initial_distribution.values()))
        print('compare to initial', ks_test.pvalue)
        print('-------------------')
        return ks_test.pvalue > self.p_value_level

    def _normalize_text(self, text):
        text = text.replace('?', '.')
        text = text.replace('!', '.')
        text = text.replace('.', '. ')

        text = text.replace('\n', ' ')
        text = text.replace('-', ' ')
        text = re.sub('[^a-zA-Z .]', '', text).lower()
        if text[-1] != '.':
            text += '.'
        return text


class Word:
    """
    Class to help handle the words transcription.
    """
    def __init__(self, text, transcription):
        self.text = text
        self.transcription = transcription

    def get_text(self):
        return self.text

    def get_transcription(self):
        return self.transcription

    def get_phonemes_count(self):
        info = {}
        for phoneme in self.transcription:
            info[phoneme] = info.get(phoneme, 0) + 1
        return info

    def get_unique_phonemes(self):
        unique_phonemes = []
        for phoneme in self.transcription:
            if phoneme not in unique_phonemes:
                unique_phonemes.append(phoneme)
        return unique_phonemes

    def get_percentage(self):
        pass
