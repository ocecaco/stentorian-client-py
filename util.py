import elementparser
from grammar import Capture, Alternative, Optional


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
            final_result = parse.value
            for f in final_result:
                f()


def mapping(name, options):
    branches = []
    for i, (child_element, child_handler) in enumerate(options):
        branches.append(Capture('@{}_choice_{}@'.format(name, i),
                                child_element, child_handler))

    element = Alternative(branches)

    def handler(node):
        return node.children[0].value

    return Capture(name, element, handler)


def choice(name, options):
    new_options = [(elementparser.parse(k), (lambda n, v=v: v))
                   for k, v in options.items()]

    return mapping(name, new_options)


def flag(name, spec):
    element = Optional(elementparser.parse(spec))

    def handler(node):
        if len(node.words) == 0:
            return False

        return True

    return Capture(name, element, handler)


def optional_default(name, child, default_value):
    element = Optional(child)

    def handler(node):
        if len(node.children) == 0:
            return default_value

        return node.children[0].value

    return Capture(name, element, handler)


class MappingBuilder(object):
    def __init__(self, name):
        self.name = name
        self.options = []

    def choice(self, spec, *captures):
        def wrap(f):
            extras = {c.capture_name: c for c in captures}
            element = elementparser.parse(spec, extras)

            def handler(node):
                return f(node, **node.by_name)

            self.options.append((element, handler))

            return f

        return wrap

    def build(self):
        return mapping(self.name, self.options)


def command_mapping(name, commands, captures):
    options = []
    for cmd, handler in commands.items():
        extras = {c.capture_name: c for c in captures}
        element = elementparser.parse(cmd, extras)
        options.append((element, handler))

    return mapping(name, options)
