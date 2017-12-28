import functools

from .grammar import Alternative, Optional, Tag, Sequence
from . import elementparser


class ActionCallback(object):
    def __init__(self, grammar):
        self.grammar = grammar

    def phrase_start(self):
        pass

    def phrase_recognition_failure(self):
        pass

    def phrase_finish(self, parse):
        extras = {}
        result = self.grammar.value(parse, extras)
        result()


def action(f):
    @functools.wraps(f)
    def handle(captures):
        def execute():
            f(captures)

        return execute

    return handle


def command(spec, handler, captures=None):
    if captures is None:
        captures = {}

    tagged = {k: Tag(element) for k, element in captures.items()}
    return _command(spec, handler, tagged)


def _command(spec, handler, tagged):
    element = elementparser.parse(spec, tagged)

    def new_handler(_parse, _child_value, extras, h=handler):
        capture_values = {k: extras[t.name]
                          for k, t in tagged.items()
                          if t.name in extras}

        return h(capture_values)

    return element.map_full(new_handler)


def mapping(commands, captures=None):
    if captures is None:
        captures = {}

    tagged = {k: Tag(element) for k, element in captures.items()}

    alternatives = [_command(spec, handler, tagged)
                    for spec, handler in commands.items()]

    return Alternative(alternatives)


def choice(cs):
    return mapping({k: lambda _e, v=v: v for k, v in cs.items()})


def flag(spec):
    element = elementparser.parse(spec)
    return Optional(element.map_value(lambda v: True), default=False)


def prefix(spec, element):
    prefix_element = elementparser.parse(spec)
    return Sequence([prefix_element, element]).map_value(lambda vs: vs[1])
