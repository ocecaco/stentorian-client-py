from grammar import Grammar, Rule, Sequence, Word, Repetition
from engine import connect
from convenience import ActionCallback, MappingBuilder, choice, flag, command_mapping, optional_default
from definitions import special_map, letter_map, format_list
from keyboard import keys, press_keys, type_string
from formatting import clean, lowercase, connect_underscore, remove_characters, split_phrases
import time


class Action(object):
    def __init__(self, steps):
        self.steps = steps

    def __add__(self, other):
        combined_steps = self.steps + other.steps
        return Action(combined_steps)

    def __call__(self):
        for s in self.steps:
            s()


numbers_1_9 = {
    "zero": 0,
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


def element_nsmall():
    return choice("nsmall", numbers_1_9).extract_rule()


def element_number(nsmall):
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


def element_printable(nsmall):
    builder = MappingBuilder('printable')

    special = choice('special', special_map)
    letter = choice('letter', letter_map)
    digit = nsmall.rename('digit')
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

    @builder.choice("(num|numb) <digit>", digit)
    def digit_handler(node, digit):
        return str(digit[0].value)

    return builder.build().extract_rule()


def element_edit(nsmall, number, printable):
    def handle_printable(node):
        named = node.by_name

        modifiers = {
            'c': 'control',
            's': 'shift',
            'a': 'alt',
            'w': 'win',
        }

        ordered = ['c', 's', 'a', 'w']

        used_modifiers = []

        for k in ordered:
            if k in named and named[k][0].value:
                used_modifiers.append(modifiers[k])

        def action():
            for m in used_modifiers:
                press_keys(m + ':down')

            if used_modifiers:
                time.sleep(0.1)

            type_string(named['printable'][0].value)

            for m in reversed(used_modifiers):
                press_keys(m + ':up')

        return action

    def handle_dictation(node):
        named = node.by_name
        words = named['text'][0].words

        formatted = connect_underscore(
            lowercase(
                remove_characters(
                    split_phrases(clean(words)))))

        def action():
            for w in formatted:
                type_string(w)

        return action

    def handle_numbers(node):
        named = node.by_name

        digits = [str(d.value) for d in named['digit']]

        def action():
            for d in digits:
                press_keys(d)

        return action

    commands = {
        "sauce <nopt>": keys('up:{nopt}'),
        "dunce <nopt>": keys('down:{nopt}'),
        "lease <nopt>": keys('left:{nopt}'),
        "Ross <nopt>": keys('right:{nopt}'),

        "page up <nopt>": keys('pageup:{nopt}'),
        "page down <nopt>": keys('pagedown:{nopt}'),
        "sauce <n> (page|pages)": keys('pageup:{n}'),
        "dunce <n> (page|pages)": keys('pagedown:{n}'),
        "lease <n> (word|words)": keys('c-left/3:{n}/10'),
        "Ross <n> (word|words)": keys('c-right/3:{n}/10'),

        "lease Wally": keys('home'),
        "Ross Wally": keys('end'),
        "sauce Wally": keys('c-home/3'),
        "dunce Wally": keys('c-end/3'),

        "ace <nopt>": keys('space:{nopt}'),
        "shock <nopt>": keys('enter:{nopt}'),
        "tabby <nopt>": keys('tab:{nopt}'),
        "deli <nopt>": keys('del:{nopt}'),
        "clear <nopt>": keys('backspace:{nopt}'),

        "escape": keys('escape'),
        "shackle": keys('c-a'),
        "stoosh": keys('c-c'),
        "spark": keys('c-j'),

        "win key": keys('win/3'),

        "hold alt": keys('alt:down/3'),
        "release alt": keys('alt:up'),
        "hold shift": keys('shift:down/3'),
        "release shift": keys('shift:up'),
        "hold control": keys('control:down/3'),
        "release control": keys('control:up'),
        "hold win": keys('win:down/3'),
        "release win": keys('win:up'),
        "release [all]": keys('alt:up, shift:up, control:up'),

        "angle": keys("langle, rangle, left/3"),
        "brax": keys("lbracket, rbracket, left/3"),
        "curly": keys("lbrace, rbrace, left/3"),
        "prekris": keys("lparen, rparen, left/3"),
        "quotes": keys("dquote/3, dquote/3, left/3"),
        "backticks": keys("backtick:2, left"),
        "thin quotes": keys("squote, squote, left/3"),

        "numbers <digit>* bow": handle_numbers,

        "[press <c> <s> <a> <w>] <printable>": handle_printable,

        "<formattype> #(text@~dictation)": handle_dictation,
    }

    captures = [
        number.rename("n"),
        nsmall.rename("digit"),
        optional_default("nopt", number, 1),
        printable.rename("printable"),
        flag("c", "control"),
        flag("s", "shift"),
        flag("a", "alt"),
        flag("w", "win|windows"),
        choice("formattype", {
            "say": "say",
        }),
    ]

    return command_mapping('edit', commands, captures)


def main():
    nsmall = element_nsmall()
    printable = element_printable(nsmall)
    number = element_number(nsmall)
    edit = element_edit(nsmall, number, printable)
    testing_rule = Rule('testing', True,
                        Sequence([Word('organization'),
                                  Repetition(edit)]))

    rules = [testing_rule]
    grammar = Grammar(rules)
    print(grammar.pretty())
    n = ActionCallback(grammar.semantics)

    with connect('192.168.2.224', 1337) as e:
        g = e.grammar_load(grammar, n)
        g.rule_activate('testing')
        e.process_notifications()


if __name__ == '__main__':
    main()
