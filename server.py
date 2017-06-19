from grammar import Grammar
from engine import connect
from convenience import ActionCallback, MappingRule, Choice


def testing(node, child_values):
    fruit = child_values[0]

    def printer():
        print(fruit)

    return printer


class TestingRule(MappingRule):
    name = 'testing'
    exported = True

    mapping = {
        "my short testing rule {mylist} <foo>": testing
    }

    captures = [
        Choice("foo", {
            "apple": "a",
            "banana": "b"
        })
    ]


class EngineCallback(object):
    def paused(self):
        print('paused')

    def microphone_state_changed(self, state):
        print(state)


def main():
    rules = []
    rules.append(TestingRule())
    grammar = Grammar(rules)
    n = ActionCallback(grammar.semantics)

    with connect('127.0.0.1', 1337) as e:
        g = e.grammar_load(grammar, n)
        g.rule_activate('testing')
        g.list_append('mylist', 'chromium')
        e.microphone_set_state('sleeping')

        r = e.register(EngineCallback())
        e.process_notifications()


if __name__ == '__main__':
    main()
