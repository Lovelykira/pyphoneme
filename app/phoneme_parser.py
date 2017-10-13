import datetime
import json
import re
import requests
from bs4 import BeautifulSoup
from scipy import stats
from subprocess import check_output


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


class HttpPhonemeParser:
    """
    Class that gets transcription for given text from http.
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


class EspeakPhonemeParser:
    """
    Class that gets transcription for given text using espeak subprocess.
    """
    def text_to_phoneme(self, text):
        return check_output(["espeak", "-q", "--ipa", '-v', 'en-us', text]).strip().decode('utf-8')


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
                    phoneme = EspeakPhonemeParser().text_to_phoneme(word)
                except Exception:
                    SavedPhonemeWords.update(saved_phoneme_words)
                    raise
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
        self.phonemes_count = {
            'single': {},
            'pairs': {},
            'triplets': {}
        }
        self.single_phonemes_count = 0
        self.pair_phonemes_count = 0
        self.triplet_phonemes_count = 0

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
        Loops through all phonemes and saves how much of each phonemes, phoneme pairs and phoneme triplets there are
        and sum of all phonemes in text.
        """
        for word_text, word_info in self.words_info.items():
            for phoneme, phoneme_count in word_info['word'].phonemes_dict['single'].items():
                occurrences = phoneme_count * word_info['count']
                self.single_phonemes_count += occurrences
                self.phonemes_count['single'][phoneme] = self.phonemes_count['single'].get(phoneme, 0) + occurrences

            for pair, pair_count in word_info['word'].phonemes_dict['pairs'].items():
                occurrences = pair_count * word_info['count']
                self.pair_phonemes_count += occurrences
                self.phonemes_count['pairs'][pair] = self.phonemes_count['pairs'].get(pair, 0) + occurrences

            for triplet, triplet_count in word_info['word'].phonemes_dict['triplets'].items():
                occurrences = triplet_count * word_info['count']
                self.triplet_phonemes_count += occurrences
                self.phonemes_count['triplets'][triplet] = self.phonemes_count['triplets'].get(triplet, 0) + occurrences

    def get_initial_percentage(self):
        """
        Calculates how much percentage does each phoneme take in initial text.
        :return: dict {
            'single': {
                'a': percentage
            },
            'pairs': {
                'ab': percentage
            },
            'triplets': {
                'abc': percentage
            }
        }
        """
        percentage = {
            'single': {},
            'pairs': {},
            'triplets': {}
        }
        for phoneme, count in self.phonemes_count['single'].items():
            percentage['single'][phoneme] = count / self.single_phonemes_count

        for pair, pair_count in self.phonemes_count['pairs'].items():
            percentage['pairs'][pair] = pair_count / self.pair_phonemes_count

        for triplet, triplet_count in self.phonemes_count['triplets'].items():
            percentage['triplets'][triplet] = triplet_count / self.triplet_phonemes_count
        return percentage

    def get_percentage(self, chunk, phonemes_num):
        """
        Calculates how much percentage does each phoneme take in given chunk of initial text.
        :param chunk: string, part of initial text
        :param phonemes_num: string, number of phonemes to get percentage - 'single', 'pairs', 'triplets'
        :return: dict {phoneme: percentage}
        """
        all_phonemes = 0
        phonemes = {}
        for word in chunk.split(' '):
            word = get_normalized_word(word)
            if not word:
                continue
            phonemes_count = self.words_info[word]['word'].phonemes_dict[phonemes_num]
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
    SYNTHESIS_APPEND = 'append'
    SYNTHESIS_DELETE = 'delete'
    MAX_PHONEME_GROUP_SIZE = 3

    def __init__(
            self, text, mode=None, p_value_level=0.7, distribution_criteria=None, synthesis_mode=None, phoneme_group_size=1
    ):
        self.text = self._normalize_text(text)
        self.p_value_level = p_value_level
        self.mode = mode if mode in self.AVAILABLE_MODES else self.DEFAULT_MODE
        self.phoneme_group_size = phoneme_group_size if phoneme_group_size <= self.MAX_PHONEME_GROUP_SIZE else 1
        self.distribution_criteria = distribution_criteria if distribution_criteria in self.AVAILABLE_CRETERIAS else self.DEFAULT_CRETERIA
        self.text_analyzer = TextAnalyzer(self.text)
        self.initial_distribution = self._get_distribution(self.text)
        self.text_distribution = None
        self.result_text = None
        self.run_time = None
        self.iterations_number = 0
        self.test_p_value_level = 0
        self.synthesis_mode = synthesis_mode or self.SYNTHESIS_APPEND
        print('self.initial_distribution', self.initial_distribution)

    def get_results(self):
        return {
            'mode': self.mode,
            'criteria': self.distribution_criteria,
            'p_value_level': self.p_value_level,
            'date': datetime.datetime.now().isoformat(),
            'initial_words': len(self.text.split(' ')),
            'result_words': len(self.result_text.split(' ')),
            'initial_distribution': self.initial_distribution,
            'result_distribution': self.text_distribution,
            'run_time': str(self.run_time),
            'iterations_number': self.iterations_number,
            'synthesis_mode': self.synthesis_mode,
            'test_p_value_level': self.test_p_value_level,
            'phoneme_group_size': self.phoneme_group_size,
            'answer': self.result_text
        }

    def synthesis(self):
        if self.synthesis_mode == self.SYNTHESIS_APPEND:
            return self.synthesize_by_appending_chunks()
        if self.synthesis_mode == self.SYNTHESIS_DELETE:
            return self.synthesize_by_deleting_chunks()

    def _get_distribution(self, chunk):
        percentage = self.text_analyzer.get_percentage(chunk, 'single')
        if self.phoneme_group_size >= 2:
            percentage.update(self.text_analyzer.get_percentage(chunk, 'pairs'))
        if self.phoneme_group_size == 3:
            percentage.update(self.text_analyzer.get_percentage(chunk, 'triplets'))
        return percentage

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
            iterations_number += 1
            loop_start = datetime.datetime.now()
            text_distribution = self._get_distribution(' '.join(text_list))
            worst_chunk = self.get_worst_chunk(chunks, text_distribution)
            if not worst_chunk:
                break
            chunks = [value for value in chunks if value != worst_chunk]
            text_list = [value for value in text_list if value != worst_chunk]

            print('iteration', iterations_number)
            print('time', datetime.datetime.now() - loop_start)
            print('removing', worst_chunk)
        print('whole time', datetime.datetime.now() - while_start)
        print('p_value_level', self.p_value_level)
        print('distribution_criteria', self.distribution_criteria)
        print('mode', self.mode)
        print('result', ' '.join(chunks))

        self.run_time = datetime.datetime.now() - while_start
        self.iterations_number = iterations_number
        self.result_text = ' '.join(chunks)
        self.text_distribution = self._get_distribution(self.result_text)
        return self.result_text

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
            iterations_number += 1
            loop_start = datetime.datetime.now()
            text_distribution = self._get_distribution(' '.join(text_list))
            best_chunk = self.get_best_chunk(chunks, text_distribution)
            if not best_chunk:
                break
            result_chunks += ' ' + best_chunk + '.'
            chunks = [value for value in chunks if value != best_chunk]
            text_list = [value for value in text_list if value != best_chunk]

            print('iteration', iterations_number)
            print('time', datetime.datetime.now() - loop_start)
            print('result', best_chunk)
        print('whole time', datetime.datetime.now() - while_start)
        print('p_value_level', self.p_value_level)
        print('distribution_criteria', self.distribution_criteria)
        print('mode', self.mode)
        print('result', result_chunks)

        self.run_time = datetime.datetime.now() - while_start
        self.iterations_number = iterations_number
        self.result_text = result_chunks
        self.text_distribution = self._get_distribution(self.result_text)
        return self.result_text

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
            chunk_distribution =  self._get_distribution(chunk)
            values_initial, values_chunk = self._get_values(text_distribution, chunk_distribution)
            ks_test = stats.ks_2samp(values_initial, values_chunk)
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
            chunk_distribution =  self._get_distribution(chunk)
            values_initial, values_chunk = self._get_values(text_distribution, chunk_distribution)
            ks_test = stats.ks_2samp(values_initial, values_chunk)
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

    def _get_values(self, initial, chunk):
        values_initial = []
        values_chunk = []

        for key in initial.keys():
            values_initial.append(initial[key])
            values_chunk.append(chunk.get(key, 0))

        return values_initial, values_chunk

    def text_is_relevant(self, text):
        """
        Compares distributions of given text and initial. Returns whether the text has similar distribution or not.
        :param text: string
        :return: bool
        """
        if not text:
            return False
        synthesis_text_distribution =  self._get_distribution(text)
        values_initial, values_chunk = self._get_values(self.initial_distribution, synthesis_text_distribution)
        ks_test = stats.ks_2samp(values_initial, values_chunk)
        print('compare to initial', ks_test.pvalue)
        print('-------------------')
        is_relevant = ks_test.pvalue >= self.p_value_level
        if is_relevant:
            self.test_p_value_level = ks_test.pvalue
        return is_relevant

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

    PROLONGATION_PHONEME = 'ː'
    SKIP_PHONEMES = ['ˈ', 'ˌ']

    def __init__(self, text, transcription):
        self.text = text
        self.transcription = [phoneme for phoneme in transcription if phoneme not in self.SKIP_PHONEMES]
        self.phonemes_dict = self.parse_phonemes_dict()

    def get_text(self):
        return self.text

    def get_transcription(self):
        return self.transcription

    def get_phonemes_count(self):
        info = {}
        for i, phoneme in enumerate(self.transcription):
            if phoneme in self.SKIP_PHONEMES:
                continue

            if self._is_next_phoneme_prolongation(i):
                phoneme += self.PROLONGATION_PHONEME
            info[phoneme] = info.get(phoneme, 0) + 1

        return info

    def parse_phonemes_dict(self):
        """
        Returns dict with number of each phoneme, phonemes pair, phoneme triplet in given word. Notice that ':' is part
        of phoneme.
        ' and ˌ are skipped.

        examples:
        "nurse": {'pairs': {'nɜː': 1, 'ɜːs': 1}, 'triplets': {'nɜːs': 1}, 'single': {'s': 1, 'ɜː': 1, 'n': 1}}
        "test": {
            'pairs': {'st': 1, 'ɛs': 1, 'tɛ': 1}, 'triplets': {'tɛs': 1, 'ɛst': 1}, 'single': {'s': 1, 't': 2, 'ɛ': 1}
        }
        :return: dict
        """
        phonemes_dict = {
            'single': dict(),
            'pairs': dict(),
            'triplets': dict()
        }

        for i, phoneme in enumerate(self.transcription):
            if phoneme == self.PROLONGATION_PHONEME:
                continue

            if self._is_next_phoneme_prolongation(i):
                phoneme += self.PROLONGATION_PHONEME
                i = i + 1

            phonemes_dict['single'][phoneme] = phonemes_dict['single'].get(phoneme, 0) + 1

            if self._next_phoneme_exists(i):
                pair = phoneme + self._next_phoneme(i)
                phonemes_dict['pairs'][pair] = phonemes_dict['pairs'].get(pair, 0) + 1

                if self._next_phoneme_exists(i+1):
                    triplet = pair + self._next_phoneme(i+1)
                    phonemes_dict['triplets'][triplet] = phonemes_dict['triplets'].get(triplet, 0) + 1
        return phonemes_dict

    def _next_phoneme(self, current_index):
        n = 2 if self._is_next_phoneme_prolongation(current_index) else 1
        phoneme = self.transcription[current_index + n]
        return phoneme + self.PROLONGATION_PHONEME if self._is_next_phoneme_prolongation(current_index + n) else phoneme

    def _next_phoneme_exists(self, current_index):
        if current_index == len(self.transcription) - 2 and self.transcription[-1] == self.PROLONGATION_PHONEME:
            return False
        return current_index < len(self.transcription) - 1

    def _is_next_phoneme_prolongation(self, current_index):
        return self._next_phoneme_exists(current_index) and self.transcription[current_index + 1] == self.PROLONGATION_PHONEME


def compare_two_texts(text1, text2):
    percentage1 = TextAnalyzer(text1).get_initial_percentage()
    percentage2 = TextAnalyzer(text2).get_initial_percentage()

    ks_test_single = stats.ks_2samp(list(percentage1['single'].values()), list(percentage2['single'].values()))
    ks_test_pairs = stats.ks_2samp(list(percentage1['pairs'].values()), list(percentage2['pairs'].values()))
    ks_test_triplets = stats.ks_2samp(list(percentage1['triplets'].values()), list(percentage2['triplets'].values()))

    print('percentage1 single', percentage1['single'])
    print('percentage2 single', percentage2['single'])

    print('percentage1 pairs', percentage1['pairs'])
    print('percentage2 pairs', percentage2['pairs'])

    print('percentage1 triplets', percentage1['triplets'])
    print('percentage2 triplets', percentage2['triplets'])

    print('single pvalue', ks_test_single.pvalue)
    print('pairs pvalue', ks_test_pairs.pvalue)
    print('triplets pvalue', ks_test_triplets.pvalue)

    print('single statistic', ks_test_single.statistic)
    print('pairs statistic', ks_test_pairs.statistic)
    print('triplets statistic', ks_test_triplets.statistic)
