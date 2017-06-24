from semantics import GrammarSemantics


def collect_rule_dependencies(rules):
    # performs a topological sort to collect rule dependencies in
    # the proper order
    dependencies = set()
    parents = set()

    to_be_processed = [(False, r) for r in rules]
    result = []

    while to_be_processed:
        is_parent, current = to_be_processed.pop()

        if is_parent:
            # we have processed all the children of this node
            parents.remove(current)
            dependencies.add(current)
            result.append(current)
        else:
            parents.add(current)

            # Place a marker so we know when we've processed all
            # the children of this node
            to_be_processed.append((True, current))

            for d in set(current.referenced_rules()):
                if d in parents:
                    raise RuntimeError('cycle in grammar rules')

                if d not in dependencies:
                    to_be_processed.append((False, d))

    return result


class Grammar(object):
    def __init__(self, rules):
        self.rules = collect_rule_dependencies(rules)

        semantics = {}
        for r in self.rules:
            for name, handler in r.capture_handlers():
                semantics[(r.name, name)] = handler

        self.semantics = GrammarSemantics(semantics)

    def serialize(self):
        serialized = {
            "rules": [r.serialize() for r in self.rules]
        }

        return serialized

    def pretty(self):
        return '\n'.join(r.pretty() for r in self.rules)


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

    def referenced_rules(self):
        yield from self.definition.referenced_rules()

    def capture_handlers(self):
        yield from self.definition.capture_handlers()

    def pretty(self):
        exp = ' (exported)' if self.exported else ''
        return self.name + exp + ' -> ' + self.definition.pretty(0) + ' ;'


class Element(object):
    def __init__(self, children):
        self.children = children

    def referenced_rules(self):
        for c in self.children:
            yield from c.referenced_rules()

    def capture_handlers(self):
        for c in self.children:
            yield from c.capture_handlers()


class Sequence(Element):
    def __init__(self, children):
        super().__init__(children)

    def serialize(self):
        return {
            "type": "sequence",
            "children": [c.serialize() for c in self.children]
        }

    def pretty(self, parent_prec):
        prec = 2
        result = ' '.join(c.pretty(prec) for c in self.children)
        if parent_prec >= prec:
            result = '(' + result + ')'

        return result


class Alternative(Element):
    def __init__(self, children):
        super().__init__(children)

    def serialize(self):
        return {
            "type": "alternative",
            "children": [c.serialize() for c in self.children]
        }

    def pretty(self, parent_prec):
        prec = 1
        result = ' | '.join(c.pretty(prec) for c in self.children)
        if parent_prec >= prec:
            result = '(' + result + ')'

        return result


class Repetition(Element):
    def __init__(self, child):
        super().__init__([child])

    def serialize(self):
        return {
            "type": "repetition",
            "child": self.children[0].serialize()
        }

    def pretty(self, parent_prec):
        prec = 3
        result = self.children[0].pretty() + '+'
        if parent_prec >= prec:
            result = '(' + result + ')'

        return result


class Optional(Element):
    def __init__(self, child):
        super().__init__([child])

    def serialize(self):
        return {
            "type": "optional",
            "child": self.children[0].serialize()
        }

    def pretty(self, parent_prec):
        return '[' + self.children[0].pretty(0) + ']'


class Capture(Element):
    def __init__(self, name, child, handler=None):
        super().__init__([child])
        self.name = name
        self.handler = handler

    def serialize(self):
        return {
            "type": "capture",
            "name": self.name,
            "child": self.children[0].serialize()
        }

    def capture_handlers(self):
        if self.handler is not None:
            yield self.name, self.handler

        yield from super().capture_handlers()

    def pretty(self, parent_prec):
        return self.children[0].pretty(parent_prec)

    @property
    def capture_name(self):
        return self.name

    def extract_rule(self):
        rule = Rule(self.name, False, self.children[0])
        new_child = RuleRef(rule)
        return Capture(self.name, new_child, self.handler)


class Word(Element):
    def __init__(self, text):
        super().__init__([])
        self.text = text

    def serialize(self):
        return {
            "type": "word",
            "text": self.text
        }

    def pretty(self, parent_prec):
        return self.text


class RuleRef(Element):
    def __init__(self, rule):
        super().__init__([])
        self.rule = rule

    def serialize(self):
        return {
            "type": "rule_ref",
            "name": self.rule.name
        }

    def referenced_rules(self):
        yield self.rule

    def pretty(self, parent_prec):
        return '&' + self.rule.name


class List(Element):
    def __init__(self, name):
        super().__init__([])
        self.name = name

    def serialize(self):
        return {
            "type": "list",
            "name": self.name
        }

    def pretty(self, parent_prec):
        return '{' + self.name + '}'


class Dictation(Element):
    def __init__(self):
        super().__init__([])

    def serialize(self):
        return {
            "type": "dictation",
        }

    def pretty(self, parent_prec):
        return '~dictation'


class DictationWord(Element):
    def __init__(self):
        super().__init__([])

    def serialize(self):
        return {
            "type": "dictation_word",
        }

    def pretty(self, parent_prec):
        return '~word'


class SpellingLetter(Element):
    def __init__(self):
        super().__init__([])

    def serialize(self):
        return {
            "type": "spelling_letter",
        }

    def pretty(self, parent_prec):
        return '~letter'


if __name__ == '__main__':
    r1 = Rule('135', False, definition=Word('hello'))
    r2 = Rule('136', True, definition=RuleRef(r1))
    r3 = Rule('137', True, definition=RuleRef(r2))
    g = Grammar([r3])
    print(g.serialize())

    print(Grammar(rules=[
        Rule(name='testing',
             exported=True,
             definition=Sequence([
                 Word("hello"),
                 Word("testing"),
                 Word("world"),
             ]))
    ]))
