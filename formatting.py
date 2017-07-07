import re

clean_regex = re.compile(r'[^A-Za-z0-9_]')


def clean(words):
    for w in words:
        first = w.split('\\', 1)[0]
        yield first


def split_phrases(words):
    for w in words:
        yield from w.split(' ')


def remove_characters(words):
    for w in words:
        yield clean_regex.sub('', w)


def lowercase(words):
    for w in words:
        yield w.lower()


def connect_underscore(words):
    yield '_'.join(words)
