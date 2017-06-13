from collections import defaultdict


class SemanticsTraversal(object):
    def __init__(self):
        self.rules = {}
        self.captures = defaultdict(dict)

    def rule(self, name, value_func):
        self.rules[name] = value_func

    def capture(self, parent_rule, name, value_func):
        self.captures[parent_rule][name] = value_func

    def _default_handler(self, node, child_values):
        return child_values

    def evaluate(self, node, parent_rule=None):
        new_parent = node.name if node.capture_type == 'rule' else parent_rule
        child_values = [self.evaluate(c, new_parent) for c in node.children]

        if node.capture_type == 'rule':
            handler = self.rules.get(node.name, self._default_handler)
            return handler(node, child_values)
        elif node.capture_type == 'capture':
            scope = self.captures.get(parent_rule, {})
            handler = scope.get(node.name, self._default_handler)
            return handler(node, child_values)
        else:
            raise RuntimeError('unknown capture type')
