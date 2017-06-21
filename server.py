from grammar import Grammar, Rule, Sequence, Word, RuleRef
from engine import connect
from convenience import ActionCallback, MappingRule, Choice


numbers_1_9 = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
}

numbers_10_19 = {
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19
}

numbers_multiple_10 = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


def create_number_rule(name):
    nsmall_rule = Rule('@{}_rule_nsmall@'.format(name), False,
                       Choice("nsmall", numbers_1_9))

    def nten(node):
        return node.children[0].value

    def nprefix(node):
        return sum(c.value for c in node.children)

    def nsmall(node):
        return node.children[0].value

    mapping = {
        "<nten>": nten,
        "<nprefix> [<nsmall>]": nprefix,
        "<nsmall>": nsmall,
    }

    extras = {
        "nten": Choice("nten", numbers_10_19),
        "nprefix": Choice("nprefix", numbers_multiple_10),
        "nsmall": RuleRef(nsmall_rule)
    }

    return MappingRule(name, False, mapping, extras)


def main():
    number_rule = create_number_rule('number')
    testing_rule = Rule('testing', True,
                        Sequence([Word('mineral'),
                                  RuleRef(number_rule)]))

    rules = []
    rules.append(testing_rule)
    grammar = Grammar(rules)
    n = ActionCallback(grammar.semantics)

    with connect('192.168.2.224', 1337) as e:
        g = e.grammar_load(grammar, n)
        g.rule_activate('testing')
        print(grammar.pretty())
        e.process_notifications()


if __name__ == '__main__':
    main()
