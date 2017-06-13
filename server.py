import elementparser
from grammar import Grammar, Rule
from engine import connect
from semantics import GrammarSemantics


def dictation(node, child_values):
    return ' '.join(node.words)


def testing(node, child_values):
    i, _ = node.child_by_name('d')
    message = 'testing: ' + child_values[i]

    def printer():
        print(message)

    return printer


meaning = GrammarSemantics()
meaning.handler('d', dictation)
meaning.handler('testing', testing)


class NotificationCallback(object):
    def phrase_start(self):
        print('start')

    def phrase_recognition_failure(self):
        print('failure')

    def phrase_finish(self, foreign, words, parse):
        if not foreign:
            v = meaning.evaluate(parse)
            print('executing semantic action')
            v()
        else:
            print('foreign: ' + ' '.join(words))


def main():
    definition = elementparser.parse('my testing grammar #(d@~dictation)')
    rule = Rule(name='testing', exported=True, definition=definition)
    grammar = Grammar([rule])

    n = NotificationCallback()

    with connect('127.0.0.1', 1337) as e:
        g = e.grammar_load(grammar, n)
        g.rule_activate('testing')
        e.process_notifications()


if __name__ == '__main__':
    main()
