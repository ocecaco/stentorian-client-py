import elementparser
from grammar import Grammar, Rule
from engine import connect
from semantics import GrammarSemantics
from convenience import ActionCallback, choice


def testing(node, child_values):
    message = 'testing: ' + str(child_values[0])

    def printer():
        print(message)

    return printer


def main():
    semantics = GrammarSemantics()

    test_element = choice(semantics, {
        "tablespoon": "a",
        "lamp": "b",
    })

    definition = elementparser.parse('my testing grammar &a',
                                     a=test_element)

    rule = Rule(name='testing', exported=True, definition=definition)

    grammar = Grammar([rule])

    n = ActionCallback(semantics)

    with connect('127.0.0.1', 1337) as e:
        g = e.grammar_load(grammar, n)
        g.rule_activate('testing')
        e.process_notifications()


if __name__ == '__main__':
    main()
