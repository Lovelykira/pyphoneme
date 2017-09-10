import datetime
import itertools
import json

import re
import requests
import numpy as np
from functools import reduce
from bs4 import BeautifulSoup
from copy import deepcopy, copy
from scipy import stats


class PhonemeParser:
    AVAILABLE_LANGUAGES = ('english', 'danish', 'german')
    DEFAULT_LANGUAGE = 'english'
    ALPHABET = 'IPA'
    URL2 = 'http://upodn.com/phon.php'
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'

    def __init__(self, language=None):
        self.language = language if language in self.AVAILABLE_LANGUAGES else self.DEFAULT_LANGUAGE

    def text_to_phoneme(self, text):
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


def get_unique_phoneme_words(text):
    words = text.split(' ')
    try:
        saved_phoneme_words_file = open("saved_phoneme_words.json", "r")
        read = saved_phoneme_words_file.read()
        phoneme_words = json.loads(read)
        saved_phoneme_words_file.close()
    except:
        phoneme_words = dict()
    for word in words:
        print(word)
        normalized_word = re.sub('[^a-zA-Z]', '', word)
        if normalized_word and normalized_word not in phoneme_words.keys():
            try:
                phoneme = PhonemeParser().text_to_phoneme(normalized_word)
            except:
                file = open("saved_phoneme_words.json", "w")
                file.write(json.dumps(phoneme_words))
                file.close()
            phoneme_words[normalized_word] = phoneme
            print('Getting phoneme for ' + normalized_word + ' - ' + phoneme)

    file = open("saved_phoneme_words.json", "w")
    file.write(json.dumps(phoneme_words))
    file.close()
    return phoneme_words


class TextAnalyzer:
    def __init__(self, text):
        self.text = text
        self.words_info = {}
        self.phonemes_count = {}
        self.all_phonemes = 0

        self.unique_phoneme_words = get_unique_phoneme_words(self.text)
        print('unique phonemes found')

        self._analyze_words()
        self._analyze_phonemes()

    def _get_words_list(self):
        text = remove_dots(self.text).split(' ')
        return remove_empty_values(text)

    def _get_words_list_phonemes(self, words):
        text = ""
        for i in range(0, len(words), 500):
            text += PhonemeParser().text_to_phoneme(self.text[i:i+500])
        text = text.split(' ')
        return remove_empty_values(text)

    def _analyze_words(self):
        words = self._get_words_list()
        # words_transcription = self._get_words_list_phonemes(words)
        # self._normalize_words_transcription(words, words_transcription)

        # for index, transcription in enumerate(words_transcription):
        for current_word in words:
            # current_word = words[index]
            if current_word in self.words_info:
                self.words_info[current_word]['count'] += 1
            else:
                transcription = self.unique_phoneme_words[current_word]
                self.words_info[current_word] = {
                    'count': 1,
                    'word': Word(current_word, transcription)
                }

    def _analyze_phonemes(self):
        for word_text, word_info in self.words_info.items():
            for phoneme, phoneme_count in word_info['word'].get_phonemes_count().items():
                self.all_phonemes += phoneme_count * word_info['count']
                self.phonemes_count[phoneme] = self.phonemes_count.get(phoneme, 0) + phoneme_count * word_info['count']

    def get_initial_percentage(self):
        percentage = {}
        for phoneme, count in self.phonemes_count.items():
            percentage[phoneme] = count / self.all_phonemes
        return percentage

    def get_percentage(self, chunk):
        chunk = remove_dots(chunk)
        # print('chunk', chunk)
        all_phonemes = 0
        phonemes = {}
        for word in remove_empty_values(chunk.split(' ')):
            word = word.strip()
            phonemes_count = self.words_info[word]['word'].get_phonemes_count()
            for phoneme, count in phonemes_count.items():
                phonemes[phoneme] = phonemes.get(phoneme, 0) + count
                all_phonemes += count

        percentage = {}
        for phoneme, count in phonemes.items():
            percentage[phoneme] = count / all_phonemes
        return percentage

    @classmethod
    def _normalize_words_transcription(cls, words, words_transcription):
        for i, word in enumerate(words):
            if i < 100:
                print(word, words_transcription[i])
            if '-' in word:
                words_transcription[i] = words_transcription[i] + words_transcription[i + 1]
                words_transcription.pop(i + 1)


class TextSynthesis:
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
        result_chunks = ''
        text = self.text
        chunks = self._get_chunks_by_mode()
        iterations_number = 0
        while not self.text_is_relevant(result_chunks):
            loop_start = datetime.datetime.now()
            text_distribution = self.text_analyzer.get_percentage(text)
            best_chunk = self.get_best_chunk(chunks, text_distribution) + '.'
            result_chunks += ' ' + best_chunk
            chunks = [value for value in chunks if value != best_chunk]
            text = text.replace(best_chunk, '')

            iterations_number += 1
            print('result', best_chunk)
            print('iteration', iterations_number)
            print('time', datetime.datetime.now() - loop_start)
        return result_chunks

    def get_best_chunk(self, chunks, text_distribution ):
        # print('get_best_chunk', text, chunks)
        chunks_ks_test = {}
        highest_p_value = -1
        highest_p_value_chunk_index = None
        smallest_statistic = 2
        smallest_statistic_chunk_index = None
        for i, chunk in enumerate(chunks):
            chunk = remove_dots(chunk)
            if not chunk:
                continue
            print('Analyzing.. ' + chunk)
            chunk_distribution = self.text_analyzer.get_percentage(chunk)
            ks_test = stats.ks_2samp(list(chunk_distribution.values()), list(text_distribution.values()))
            chunks_ks_test[i] = ks_test

            if ks_test.statistic < smallest_statistic:
                smallest_statistic = ks_test.statistic
                smallest_statistic_chunk_index = i
            if ks_test.pvalue > highest_p_value:
                highest_p_value = ks_test.pvalue
                highest_p_value_chunk_index = i

        if self.distribution_criteria == self.PVALUE:
            return chunks[highest_p_value_chunk_index]
        if self.distribution_criteria == self.STATISTIC:
            return chunks[smallest_statistic_chunk_index]

    def _get_chunks_by_mode(self):
        if self.mode == self.SENTENCE:
            return self.text.split('.')
        if self.mode == self.WORD:
            return self.text_analyzer.unique_phoneme_words.keys()

        # highest_p_value_chunk = chunks_ks_test[highest_p_value_chunk_index]
        # smallest_statistic_chunk = chunks_ks_test[smallest_statistic_chunk_index]

        # if highest_p_value_chunk == smallest_statistic_chunk:
        #     return chunks[highest_p_value_chunk_index]
        #
        # #if p_value is closer to 1 than statistic to 0
        # if 1 - highest_p_value_chunk.p_value < smallest_statistic_chunk.statistic:
        #     return chunks[highest_p_value_chunk_index]
        # return chunks[smallest_statistic_chunk_index]

    def text_is_relevant(self, text):
        if not text:
            return False
        synthesis_text_distribution = self.text_analyzer.get_percentage(text)
        # print('initial_distribution', self.initial_distribution)
        # print('synthesis_text_distribution', synthesis_text_distribution)
        ks_test = stats.ks_2samp(list(synthesis_text_distribution.values()), list(self.initial_distribution.values()))
        # print('==========')
        # print('ks_test', ks_test)
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



class Sentence:
    def __init__(self):
        pass


def entropy(*X):
    return np.sum(-p * np.log2(p) if p > 0 else 0 for p in
        (np.mean(reduce(np.logical_and, (predictions == c for predictions, c in zip(X, classes))))
            for classes in itertools.product(*[set(x) for x in X])))