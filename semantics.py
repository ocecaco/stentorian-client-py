from collections import defaultdict


def _default_handler(node, child_values):
    if len(child_values) == 1:
        return child_values[0]

    return child_values


class GrammarSemantics(object):
    def __init__(self):
        self.rules = defaultdict(lambda: _default_handler)

    def handler(self, name, semantics):
        if name.startswith('_'):
            raise RuntimeError(('cannot add handler for capture name'
                                ' that starts with an underscore'
                                ' because name is not guaranteed to'
                                ' be unique in the grammar'))

        self.rules[name] = semantics

    def evaluate(self, node):
        child_values = [self.evaluate(c) for c in node.children]
        handler = self.rules[node.name]
        return handler(node, child_values)
