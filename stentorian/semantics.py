from collections import defaultdict


def _default_handler(node):
    return [c.value for c in node.children]


class GrammarSemantics(object):
    def __init__(self, rules):
        self.rules = defaultdict(lambda: _default_handler, rules)

    def annotate_values(self, node):
        for c in node.children:
            self.annotate_values(c)

        handler = self.rules[(node.rule, node.name)]
        result = handler(node)
        node.value = result
