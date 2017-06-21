import elementparser
from grammar import Capture, Alternative, Optional, Rule


class ActionCallback(object):
    def __init__(self, semantics):
        self.semantics = semantics

    def phrase_start(self):
        pass

    def phrase_recognition_failure(self):
        pass

    def phrase_finish(self, foreign, words, parse):
        if not foreign:
            self.semantics.annotate_values(parse)
            print(parse.value)


class Mapping(Capture):
    def __init__(self, name, options, extras={}):
        branches = []
        for i, (k, v) in enumerate(options.items()):
            child = elementparser.parse(k, **extras)
            branches.append(Capture('@{}_choice_{}@'.format(name, i),
                                    child, v))

        element = Alternative(branches)

        def handler(node):
            return node.children[0].value

        super().__init__(name, element, handler)


class Choice(Mapping):
    def __init__(self, name, options, extras={}):
        new_options = {k: (lambda n, v=v: v) for k, v in options.items()}
        super().__init__(name, new_options, extras)


class Flag(Capture):
    def __init__(self, name, element):
        def handler(node):
            if len(node.words) == 0:
                return False

            return True

        super().__init__(name, Optional(element), handler)


class MappingRule(Rule):
    def __init__(self, name=None, exported=None, mapping=None, extras=None):
        if name is None:
            name = self.name
        if exported is None:
            exported = self.exported
        if mapping is None:
            mapping = self.mapping
        if extras is None:
            extras = self.extras

        definition = Mapping(name, mapping, extras)
        super().__init__(name, exported, definition)
