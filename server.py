from grammar import Grammar, Rule, Sequence, Word, RuleRef, Capture
from engine import connect
from convenience import ActionCallback, MappingBuilder, choice
from definitions import special_map, letter_map, format_list


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


def create_nsmall():
    return choice("nsmall", numbers_1_9).extract_rule()


def create_number(nsmall):
    number = MappingBuilder('number')

    nten = choice("nten", numbers_10_19)
    nprefix = choice("nprefix", numbers_multiple_10)

    @number.choice("<nten>", nten)
    def nten_handler(node, nten):
        return nten[0].value

    @number.choice("<nprefix> [<nsmall>]", nprefix, nsmall)
    def nprefix_handler(node, nprefix, nsmall=None):
        small = 0 if nsmall is None else nsmall[0].value
        return nprefix[0].value + small

    @number.choice("<nsmall>", nsmall)
    def nsmall_handler(node, nsmall):
        return nsmall[0].value

    return number.build().extract_rule()


def create_printable(nsmall):
    builder = MappingBuilder('printable')

    special = choice('special', special_map)
    letter = choice('letter', letter_map)
    pair = choice('pair', {
        "angle": "<>",
        "brax": "[]",
        "curly": "{}",
        "prekris": "()",
    })
    side = choice('side', {
        "left": 0,
        "right": 1,
    })

    @builder.choice("<side> <pair>", pair, side)
    def pair_handler(node, side, pair):
        characters = pair[0].value
        idx = side[0].value
        return characters[idx]

    @builder.choice("<special>", special)
    def special_handler(node, special):
        return special[0].value

    @builder.choice("#(b@[big]) <letter>", letter)
    def letter_handler(node, b, letter):
        result = letter[0].value

        if len(b[0].words) != 0:
            return result.upper()

        return result

    @builder.choice("(num|numb) <nsmall>", nsmall)
    def digit_handler(node, nsmall):
        return str(nsmall[0].value)

    return builder.build().extract_rule()


# matching = {
#     "angle": "<>",
#     "brax": "[]",
#     "curly": "{}",
#     "prekris": "()",
#     "quotes": '""',
#     "backticks": "``",
#     "thin quotes": "''",
# }

# functional = {
#     "ace": "space",
#     "shock": "enter",
#     "tabby": "tab",
#     "deli": "delete",
#     "clear": "backspace",
# }


# builder = MappingBuilder('genericedit')


# @builder.choice("<direction> (Wally|[<n>])")
# def arrows(node):
#     pass


# @builder.choice("page (up|down) [<n>]")
# def pages(node):
#     pass


# @builder.choice("<functional> [<n>]")
# def functional(node):
#     pass


# @builder.choice("escape")
# def escape(node):
#     pass


# @builder.choice("shackle")
# def shackle(node):
#     pass


# @builder.choice("stoosh")
# def stoosh(node):
#     pass


# @builder.choice("spark")
# def spark(node):
#     pass


# @builder.choice("#(k@hold|release) #(mod@control|shift|alt|win)")
# def modifiers(node):
#     pass


# @builder.choice("release all")
# def release(node):
#     pass


# @builder.choice("[press [#(c@control)] [#(s@shift)] [#(a@alt)] [#(w@win)]] <key>")
# def press_key(node):
#     pass


# @builder.choice("<matching> [<n>]")
# def matching(node):
#     pass


# @builder.choice("<format> ~dictation")
# def format_text(node):
#     pass


# extras = # {
#     "n": Capture("n", RuleRef(number_rule)),
#     "functional": Choice("functional", functional),
#     "matching": Choice("matching", matching),
#     "format": Choice("format", {
#         "say": lambda words: ' '.join(words)
#     }),
#     "direction": Choice("direction", {
#         "lease": "left",
#         "Ross": "right",
#         "sauce": "up",
#         "dunce": "down",
#     }),
#     "key": Choice("key", {
#         "arch": "a"
#     }),
# }


def main():
    digit_rule = create_nsmall()
    printable_rule = create_printable(digit_rule)
    testing_rule = Rule('testing', True,
                        Sequence([Word('organization'),
                                  printable_rule]))

    rules = [testing_rule]
    grammar = Grammar(rules)
    n = ActionCallback(grammar.semantics)

    with connect('192.168.2.224', 1337) as e:
        g = e.grammar_load(grammar, n)
        g.rule_activate('testing')
        print(grammar.pretty())
        e.process_notifications()


if __name__ == '__main__':
    main()
