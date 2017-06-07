import json
from collections import namedtuple


GrammarBase = namedtuple('Grammar', ['rules'])


class Grammar(GrammarBase):
    def serialize(self):
        return {
            "rules": [r.serialize() for r in self.rules]
        }

    def json(self):
        return json.dumps(self.serialize())


RuleBase = namedtuple('Rule', ['name', 'exported', 'definition'])


class Rule(RuleBase):
    def serialize(self):
        return {
            "name": self.name,
            "exported": self.exported,
            "definition": self.definition.serialize()
        }


SequenceBase = namedtuple('Sequence', ['children'])


class Sequence(SequenceBase):
    def serialize(self):
        return {
            "type": "sequence",
            "children": [c.serialize() for c in self.children]
        }


AlternativeBase = namedtuple('Alternative', ['children'])


class Alternative(AlternativeBase):
    def serialize(self):
        return {
            "type": "alternative",
            "children": [c.serialize() for c in self.children]
        }


RepetitionBase = namedtuple('Repetition', ['child'])


class Repetition(RepetitionBase):
    def serialize(self):
        return {
            "type": "repetition",
            "child": self.child.serialize()
        }


OptionalBase = namedtuple('Optional', ['child'])


class Optional(OptionalBase):
    def serialize(self):
        return {
            "type": "optional",
            "child": self.child.serialize()
        }


CaptureBase = namedtuple('Capture', ['name', 'child'])


class Capture(CaptureBase):
    def serialize(self):
        return {
            "type": "capture",
            "name": self.name,
            "child": self.child.serialize()
        }


WordBase = namedtuple('Word', ['text'])


class Word(WordBase):
    def serialize(self):
        return {
            "type": "word",
            "text": self.text
        }


RuleRefBase = namedtuple('RuleRef', ['name'])


class RuleRef(RuleRefBase):
    def serialize(self):
        return {
            "type": "rule_ref",
            "name": self.name
        }


ListBase = namedtuple('List', ['name'])


class List(ListBase):
    def serialize(self):
        return {
            "type": "list",
            "name": self.name
        }


DictationBase = namedtuple('Dictation', [])


class Dictation(DictationBase):
    def serialize(self):
        return {
            "type": "dictation",
        }


DictationWordBase = namedtuple('DictationWord', [])


class DictationWord(DictationWordBase):
    def serialize(self):
        return {
            "type": "dictation_word",
        }


SpellingLetterBase = namedtuple('SpellingLetter', [])


class SpellingLetter(SpellingLetterBase):
    def serialize(self):
        return {
            "type": "spelling_letter",
        }


if __name__ == '__main__':
    print(Grammar(rules=[
        Rule(name='testing',
             exported=True,
             definition=Sequence([
                 Word("hello"),
                 Word("testing"),
                 Word("world"),
             ]))
    ]))
