from grammar import (Alternative, Sequence, Repetition,
                     Optional, Word, Capture, List, RuleRef,
                     Dictation, DictationWord, SpellingLetter)


class GrammarParser(object):
    def __init__(self, s, **extras):
        self._s = s
        self._pos = 0

        self._extras = extras

    def parse(self):
        return self._element()

    def _skip_spaces(self):
        while self._pos != len(self._s) and self._s[self._pos].isspace():
            self._pos += 1

    def _token(self, token):
        t = self._next()
        assert(t == token)

    def _next(self, skip=True):
        t = self._peek(skip)
        if t is not None:
            self._pos += 1
        return t

    def _peek(self, skip=True):
        if self._pos == len(self._s):
            return None

        if skip:
            self._skip_spaces()

        return self._s[self._pos]

    def _eof(self):
        assert(self._pos == len(self._s))

    def _element(self):
        element = self._alternative()
        self._eof()
        return element

    def _alternative(self):
        options = []
        options.append(self._sequence())
        while self._peek() == '|':
            self._token('|')
            options.append(self._sequence())

        if len(options) == 1:
            return options[0]
        else:
            return Alternative(options)

    def _sequence(self):
        children = []
        children.append(self._mayberepetition())
        sequence_start = set(['[', '<', '{', '#', '(', '`', '&', '~'])
        t = self._peek()
        while t is not None and (t in sequence_start or t.isalnum()):
            children.append(self._mayberepetition())
            t = self._peek()

        if len(children) == 1:
            return children[0]
        else:
            return Sequence(children)

    def _mayberepetition(self):
        child = self._atom()
        if self._peek() == '*':
            self._token('*')
            return Repetition(child)
        else:
            return child

    def _atom(self):
        t = self._peek()
        if t == '[':
            return self._optional()
        elif t == '<':
            return self._ruleref()
        elif t == '{':
            return self._list()
        elif t == '#':
            return self._capture()
        elif t == '(':
            self._token('(')
            a = self._alternative()
            self._token(')')
            return a
        elif t == '&':
            return self._splice()
        elif t == '~':
            return self._special()
        else:
            return Word(self._word())

    def _special(self):
        self._token('~')
        w = self._word()
        rules = {
            'dictation': Dictation(),
            'word': DictationWord(),
            'letter': SpellingLetter()
        }
        return rules[w]

    def _splice(self):
        self._token('&')
        w = self._word()
        return self._extras[w]

    def _optional(self):
        self._token('[')
        child = self._alternative()
        self._token(']')
        return Optional(child)

    def _ruleref(self):
        self._token('<')
        w = self._word()
        self._token('>')
        return RuleRef(w)

    def _list(self):
        self._token('{')
        w = self._word()
        self._token('}')
        return List(w)

    def _capture(self):
        self._token('#')
        self._token('(')
        name = self._word()
        self._token('@')
        child = self._alternative()
        self._token(')')
        return Capture(name, child)

    def _word(self):
        t = self._peek()
        if t == '`':
            self._token('`')
            word = []
            while self._peek(skip=False) != '`':
                word.append(self._next(skip=False))
            self._token('`')
            return ''.join(word)
        else:
            word = []
            t = self._peek(skip=False)
            while t is not None and t.isalnum():
                word.append(self._next(skip=False))
                t = self._peek(skip=False)
            return ''.join(word)


def parse(s, **extras):
    p = GrammarParser(s, **extras)
    return p.parse()


def main():
    print(parse('snake case ~dictation').serialize())


if __name__ == '__main__':
    main()
