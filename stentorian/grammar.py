def collect_rule_dependencies(rules):
    # performs a topological sort to collect rule dependencies in
    # the proper order
    processed = set()
    parents = set()

    to_be_processed = [(False, r) for r in rules]
    result = []

    while to_be_processed:
        is_parent, current = to_be_processed.pop()

        if current in processed:
            continue

        if is_parent:
            # we have processed all the children of this node
            parents.remove(current)
            result.append(current)
            processed.add(current)
        else:
            parents.add(current)

            # Place a marker so we know when we've processed all
            # the children of this node
            to_be_processed.append((True, current))

            for d in set(current.referenced_rules()):
                if d in parents:
                    raise RuntimeError('cycle in grammar rules')

                if d not in processed:
                    to_be_processed.append((False, d))

    return result


def wrap(name, child):
    return {
        "type": "capture",
        "name": name,
        "child": child
    }


class ParseContext(object):
    def __init__(self, parse_tree, control, extras):
        self.parse_tree = parse_tree
        self.control = control
        self.extras = extras

    @property
    def children(self):
        return [ParseContext(c, self.control, self.extras)
                for c in self.parse_tree.children]


class Grammar(object):
    def __init__(self, rules):
        self.rules = collect_rule_dependencies(rules)
        self.rule_map = {r.name: r for r in self.rules}

    def serialize(self):
        serialized = {
            "rules": [r.serialize() for r in self.rules]
        }

        return serialized

    def value(self, context):
        rule_name = context.parse_tree.name
        return self.rule_map[rule_name].value(context)

    def on_load(self, control):
        for r in self.rules:
            r.on_load(control)

    def pretty(self):
        return '\n'.join(r.pretty() for r in self.rules)


class Rule(object):
    rule_counter = 0

    def __init__(self, definition, exported):
        self.name = 'rule_' + str(Rule.rule_counter)
        Rule.rule_counter += 1
        self.exported = exported
        self.definition = definition

    def serialize(self):
        return {
            "name": self.name,
            "exported": self.exported,
            "definition": wrap(self.name, self.definition.serialize())
        }

    def value(self, context):
        return self.definition.value(context.children[0])

    def referenced_rules(self):
        yield from self.definition.referenced_rules()

    def on_load(self, control):
        self.definition._on_load_recursive(control)

    def pretty(self):
        exp = ' (exported)' if self.exported else ''
        return self.name + exp + ' -> ' + self.definition.pretty(0) + ' ;'


class Element(object):
    def __init__(self, children):
        self.children = children

    def map_value(self, handler):
        return Map(lambda value, context: handler(value), self)

    def map_full(self, handler):
        return Map(handler, self)

    def referenced_rules(self):
        for c in self.children:
            yield from c.referenced_rules()

    def on_load(self, control):
        pass

    def _on_load_recursive(self, control):
        self.on_load(control)

        for c in self.children:
            c._on_load_recursive(control)


class Tag(Element):
    tag_counter = 0

    def __init__(self, child):
        super().__init__([child])
        self.name = 'tag_' + str(Tag.tag_counter)
        Tag.tag_counter += 1

    def serialize(self):
        return self.children[0].serialize()

    def value(self, context):
        child_value = self.children[0].value(context)
        context.extras[self.name] = child_value
        return child_value

    def pretty(self, parent_prec):
        return self.children[0].pretty(parent_prec)


class Map(Element):
    def __init__(self, handler, child):
        super().__init__([child])
        self.handler = handler

    def serialize(self):
        return self.children[0].serialize()

    def value(self, context):
        child_value = self.children[0].value(context)
        return self.handler(child_value, context)

    def pretty(self, parent_prec):
        return self.children[0].pretty(parent_prec)


class Sequence(Element):
    TAG = 'seq'

    def serialize(self):
        return wrap(self.TAG, {
            "type": "sequence",
            "children": [c.serialize() for c in self.children]
        })

    def value(self, context):
        child_values = [c.value(c_parse)
                        for c, c_parse in zip(self.children, context.children)]

        return child_values

    def pretty(self, parent_prec):
        prec = 2
        result = ' '.join(c.pretty(prec) for c in self.children)
        if parent_prec >= prec:
            result = '(' + result + ')'

        return result


class Alternative(Element):
    TAG = 'alt'

    def serialize(self):
        return {
            "type": "alternative",
            "children": [wrap(self.TAG + str(i), c.serialize())
                         for i, c in enumerate(self.children)]
        }

    def value(self, context):
        # get the index of the child that was matched
        i = int(context.parse_tree.name[len(self.TAG):])

        return self.children[i].value(context.children[0])

    def pretty(self, parent_prec):
        prec = 1
        result = ' | '.join(c.pretty(prec) for c in self.children)
        if parent_prec >= prec:
            result = '(' + result + ')'

        return result


class Repetition(Element):
    TAG = 'rep'

    def __init__(self, child):
        super().__init__([child])

    def serialize(self):
        return wrap(self.TAG, {
            "type": "repetition",
            "child": self.children[0].serialize()
        })

    def value(self, context):
        child = self.children[0]
        child_values = [child.value(c_parse) for c_parse in context.children]
        return child_values

    def pretty(self, parent_prec):
        prec = 3
        result = self.children[0].pretty(prec) + '*'
        if parent_prec >= prec:
            result = '(' + result + ')'

        return result


class Optional(Element):
    TAG = 'opt'

    def __init__(self, child, default=None):
        super().__init__([child])
        self.default = default

    def serialize(self):
        return wrap(self.TAG, {
            "type": "optional",
            "child": self.children[0].serialize()
        })

    def value(self, context):
        if not context.children:
            return self.default

        return self.children[0].value(context.children[0])

    def pretty(self, _parent_prec):
        return '[' + self.children[0].pretty(0) + ']'


def leaf_wrap(child):
    return wrap('leaf', child)


class RuleRef(Element):
    def __init__(self, rule):
        super().__init__([])
        self.rule = rule

    def serialize(self):
        return {
            "type": "rule_ref",
            "name": self.rule.name
        }

    def value(self, context):
        return self.rule.value(context)

    def referenced_rules(self):
        yield self.rule

    def pretty(self, _parent_prec):
        return '&' + self.rule.name


class Word(Element):
    def __init__(self, text):
        super().__init__([])
        self.text = text

    def serialize(self):
        return leaf_wrap({
            "type": "word",
            "text": self.text
        })

    def value(self, context):
        assert len(context.parse_tree.words) == 1
        return context.parse_tree.words[0]

    def pretty(self, _parent_prec):
        return self.text


class List(Element):
    counter = 0

    def __init__(self, initial=None):
        super().__init__([])
        self.name = 'list_' + str(List.counter)
        self.initial = initial
        List.counter += 1

    def serialize(self):
        return leaf_wrap({
            "type": "list",
            "name": self.name
        })

    def value(self, context):
        assert len(context.parse_tree.words) == 1
        return context.parse_tree.words[0]

    def on_load(self, control):
        if not self.initial:
            return

        for word in self.initial:
            control.list_append(self, word)

    def pretty(self, _parent_prec):
        return '{' + self.name + '}'


class Dictation(Element):
    def __init__(self):
        super().__init__([])

    def serialize(self):
        return leaf_wrap({
            "type": "dictation",
        })

    def value(self, context):
        return context.parse_tree.words

    def pretty(self, _parent_prec):
        return '~dictation'


class DictationWord(Element):
    def __init__(self):
        super().__init__([])

    def serialize(self):
        return leaf_wrap({
            "type": "dictation_word",
        })

    def value(self, context):
        assert len(context.parse_tree.words) == 1
        return context.parse_tree.words[0]

    def pretty(self, _parent_prec):
        return '~word'


class SpellingLetter(Element):
    def __init__(self):
        super().__init__([])

    def serialize(self):
        return leaf_wrap({
            "type": "spelling_letter",
        })

    def value(self, context):
        assert len(context.parse_tree.words) == 1
        return context.parse_tree.words[0]

    def pretty(self, _parent_prec):
        return '~letter'
