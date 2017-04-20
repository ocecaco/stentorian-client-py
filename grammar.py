import json


class Grammar(object):
    def __init__(self, rules):
        self.rules = rules

    def serialize(self):
        return {
            "rules": [r.serialize() for r in self.rules]
        }

    def json(self):
        return json.dumps(self.serialize())


class Rule(object):
    def __init__(self, name, exported, definition):
        self.name = name
        self.exported = exported
        self.definition = definition

    def serialize(self):
        return {
            "name": self.name,
            "exported": self.exported,
            "definition": self.definition.serialize()
        }


class Sequence(object):
    def __init__(self, children):
        self.children = children

    def serialize(self):
        return {
            "type": "sequence",
            "children": [c.serialize() for c in self.children]
        }


class Alternative(object):
    def __init__(self, children):
        self.children = children

    def serialize(self):
        return {
            "type": "alternative",
            "children": [c.serialize() for c in self.children]
        }


class Repetition(object):
    def __init__(self, child):
        self.child = child

    def serialize(self):
        return {
            "type": "repetition",
            "child": self.child.serialize()
        }


class Optional(object):
    def __init__(self, child):
        self.child = child

    def serialize(self):
        return {
            "type": "optional",
            "child": self.child.serialize()
        }


class Capture(object):
    def __init__(self, key, child):
        self.key = key
        self.child = child

    def serialize(self):
        return {
            "type": "capture",
            "key": self.key,
            "child": self.child.serialize()
        }


class Word(object):
    def __init__(self, text):
        self.text = text

    def serialize(self):
        return {
            "type": "word",
            "text": self.text
        }


class RuleRef(object):
    def __init__(self, name):
        self.name = name

    def serialize(self):
        return {
            "type": "rule_ref",
            "name": self.name
        }


class List(object):
    def __init__(self, name):
        self.name = name

    def serialize(self):
        return {
            "type": "list",
            "name": self.name
        }


class Dictation(object):
    def serialize(self):
        return {
            "type": "dictation",
        }


class DictationWord(object):
    def serialize(self):
        return {
            "type": "dictation_word",
        }


class SpellingLetter(object):
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
    ]).json())
