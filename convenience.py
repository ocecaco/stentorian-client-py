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
            v = self.semantics.evaluate(parse)
            v()


class Mapping(Capture):
    def __init__(self, name, options, captures={}):
        branches = []
        for i, (k, v) in enumerate(options.items()):
            child = elementparser.parse(k, **captures)
            branches.append(Capture('@{}_choice_{}@'.format(name, i),
                                    child, v))

        element = Alternative(branches)

        def handler(node, child_values):
            return child_values[0]

        super().__init__(name, element, handler)


class Choice(Mapping):
    def __init__(self, name, options, captures={}):
        new_options = {k: (lambda n, c, v=v: v) for k, v in options.items()}
        super().__init__(name, new_options, captures)


class Flag(Capture):
    def __init__(self, name, element):
        def handler(node, child_values):
            if len(node.words) == 0:
                return False

            return True

        super().__init__(name, Optional(element), handler)


class MappingRule(Rule):
    def __init__(self, name=None, exported=None, mapping=None, captures=None):
        if name is None:
            name = self.name
        if exported is None:
            exported = self.exported
        if mapping is None:
            mapping = self.mapping
        if captures is None:
            captures = self.captures

        captures = {c.capture_name: c for c in captures}
        definition = Mapping(name, mapping, captures)
        super().__init__(name, exported, definition)
