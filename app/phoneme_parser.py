import itertools

import numpy as np
from functools import reduce


from copy import deepcopy, copy

import requests
from bs4 import BeautifulSoup


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


class TextAnalyzer:
    def __init__(self, text):
        self.text = text.strip()
        self.words_info = {}
        self.phonemes_count = {}
        self.all_phonemes = 0

        self._analyze_words()
        self._analyze_phonemes()

    def _get_words_list(self):
        return self.text.split(' ')

    def _get_words_list_phonemes(self):
        phonemes = PhonemeParser().text_to_phoneme(self.text)
        return phonemes.split(' ')

    def _analyze_words(self):
        words = self._get_words_list()
        words_transcription = self._get_words_list_phonemes()

        for index, transcription in enumerate(words_transcription):
            if transcription == '':
                continue

            current_word = words[index]
            if current_word in self.words_info:
                self.words_info[current_word]['count'] += 1
            else:
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


class TextSynthesis:
    def __init__(self, text):
        self.text = text
        self.text_analyzer = TextAnalyzer(text)
        self.initial_distribution = self.text_analyzer.get_initial_percentage()

    def synthesize_using_words(self):
        words = copy(self.text_analyzer.words_info)
        all_phonemes = self.text_analyzer.all_phonemes

        result_words = []
        while not self.text_is_relevant(result_words):
            relevant_word = self.get_most_relevant_word(words)
            words.pop(relevant_word)
            result_words.append(relevant_word)
        return result_words

    def get_most_relevant_word(self, words):
        for word, word_info in words.items():
            word_info['word'].get_percentage()


    def text_is_relevant(self, words):
        return words != []


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