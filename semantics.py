from collections import defaultdict


def _default_handler(node, child_values):
    return child_values


class GrammarSemantics(object):
    def __init__(self, rules):
        self.rules = defaultdict(lambda: _default_handler, rules)

    def evaluate(self, node):
        child_values = [self.evaluate(c) for c in node.children]
        handler = self.rules[(node.rule, node.name)]
        result = handler(node, child_values)
        return result
