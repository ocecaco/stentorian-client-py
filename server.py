import elementparser
from grammar import Grammar, Rule
from engine import connect


class NotificationCallback(object):
    def phrase_start(self):
        print('start')

    def phrase_recognition_failure(self):
        print('failure')

    def phrase_finish(self, foreign, words, parse):
        if not foreign:
            print(' '.join(parse.child_by_name('d').words))
        else:
            print('foreign: ' + ' '.join(words))


def main():
    definition = elementparser.parse('my testing grammar #(d@~dictation)')
    rule = Rule(name='testing', exported=True, definition=definition)
    grammar = Grammar([rule])

    n = NotificationCallback()

    with connect('127.0.0.1', 1337) as e:
        g = e.grammar_load(grammar, True, n)
        g.rule_activate('testing')
        e.process_notifications()


if __name__ == '__main__':
    main()
