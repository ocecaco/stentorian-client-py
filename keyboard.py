from keystroke import parse_keystroke
import time
from pykeyboard import PyKeyboard
import string


class KeyboardWrapper(object):
    def __init__(self, keyboard):
        self.keyboard = keyboard

        self.key_mapping = create_key_mapping(self.keyboard)

    def _key_action(self, key):
        actual_key = self.key_mapping[key.key]
        delay_multiplier = 0.01

        sorted_modifiers = [('c', self.keyboard.control_key),
                            ('s', self.keyboard.shift_key),
                            ('a', self.keyboard.alt_key),
                            ('w', self.keyboard.windows_l_key)]

        modifier_keys = [v for k, v in sorted_modifiers
                         if k in key.modifiers]

        if key.direction is None:
            for k in modifier_keys:
                self.keyboard.press_key(k)

            for _ in range(key.repeat):
                self.keyboard.tap_key(actual_key)
                time.sleep(delay_multiplier * key.inner)

            for k in reversed(modifier_keys):
                self.keyboard.release_key(k)

            time.sleep(delay_multiplier * key.outer)
        elif key.direction == 'down':
            self.keyboard.press_key(actual_key)
            time.sleep(delay_multiplier * key.outer)
        elif key.direction == 'up':
            self.keyboard.release_key(actual_key)
            time.sleep(delay_multiplier * key.outer)

    def keys(self, spec):
        ks = (parse_keystroke(s.strip()) for s in spec.split(','))

        for k in ks:
            self._key_action(k)


def create_key_mapping(keyboard):
    key_mapping = {}

    for letter in string.ascii_letters:
        key_mapping[letter] = letter

    for digit in string.digits:
        key_mapping[digit] = digit

    typeables = {
        "zero":           '0',
        "one":            '1',
        "two":            '2',
        "three":          '3',
        "four":           '4',
        "five":           '5',
        "six":            '6',
        "seven":          '7',
        "eight":          '8',
        "nine":           '9',

        "bang":           '!',
        "exclamation":    '!',
        "at":             '@',
        "hash":           '#',
        "dollar":         '$',
        "percent":        '%',
        "caret":          '^',
        "and":            '&',
        "ampersand":      '&',
        "star":           '*',
        "asterisk":       '*',
        "leftparen":      '(',
        "lparen":         '(',
        "rightparen":     ')',
        "rparen":         ')',
        "minus":          '-',
        "hyphen":         '-',
        "underscore":     '_',
        "plus":           '+',
        "backtick":       '`',
        "tilde":          '~',
        "leftbracket":    '[',
        "lbracket":       '[',
        "rightbracket":   ']',
        "rbracket":       ']',
        "leftbrace":      '{',
        "lbrace":         '{',
        "rightbrace":     '}',
        "rbrace":         '}',
        "backslash":      '\\',
        "bar":            '|',
        "colon":          ':',
        "semicolon":      ';',
        "apostrophe":     '"',
        "singlequote":    "'",
        "squote":         "'",
        "quote":          '"',
        "doublequote":    '"',
        "dquote":         '"',
        "comma":          ',',
        "dot":            '.',
        "slash":          '/',
        "lessthan":       '<',
        "leftangle":      '<',
        "langle":         '<',
        "greaterthan":    '>',
        "rightangle":     '>',
        "rangle":         '>',
        "question":       '?',
        "equal":          '=',
        "equals":         '=',

        "enter":          keyboard.enter_key,
        "tab":            keyboard.tab_key,
        "space":          keyboard.space_key,
        "backspace":      keyboard.backspace_key,
        "delete":         keyboard.delete_key,
        "del":            keyboard.delete_key,
        "shift":          keyboard.shift_key,
        "control":        keyboard.control_key,
        "ctrl":           keyboard.control_key,
        "alt":            keyboard.alt_key,
        "escape":         keyboard.escape_key,
        "insert":         keyboard.insert_key,
        "pause":          keyboard.pause_key,
        "win":            keyboard.windows_l_key,
        "apps":           keyboard.apps_key,
        "popup":          keyboard.apps_key,
        "up":             keyboard.up_key,
        "down":           keyboard.down_key,
        "left":           keyboard.left_key,
        "right":          keyboard.right_key,
        "pageup":         keyboard.page_up_key,
        "pgup":           keyboard.page_up_key,
        "pagedown":       keyboard.page_down_key,
        "pgdown":         keyboard.page_down_key,
        "home":           keyboard.home_key,
        "end":            keyboard.end_key,
        "npmul":          keyboard.numpad_keys['Multiply'],
        "npadd":          keyboard.numpad_keys['Add'],
        "npsep":          keyboard.numpad_keys['Separator'],
        "npsub":          keyboard.numpad_keys['Subtract'],
        "npdec":          keyboard.numpad_keys['Decimal'],
        "npdiv":          keyboard.numpad_keys['Divide'],
        "numpad0":        keyboard.numpad_keys[0],
        "np0":            keyboard.numpad_keys[0],
        "numpad1":        keyboard.numpad_keys[1],
        "np1":            keyboard.numpad_keys[1],
        "numpad2":        keyboard.numpad_keys[2],
        "np2":            keyboard.numpad_keys[2],
        "numpad3":        keyboard.numpad_keys[3],
        "np3":            keyboard.numpad_keys[3],
        "numpad4":        keyboard.numpad_keys[4],
        "np4":            keyboard.numpad_keys[4],
        "numpad5":        keyboard.numpad_keys[5],
        "np5":            keyboard.numpad_keys[5],
        "numpad6":        keyboard.numpad_keys[6],
        "np6":            keyboard.numpad_keys[6],
        "numpad7":        keyboard.numpad_keys[7],
        "np7":            keyboard.numpad_keys[7],
        "numpad8":        keyboard.numpad_keys[8],
        "np8":            keyboard.numpad_keys[8],
        "numpad9":        keyboard.numpad_keys[9],
        "np9":            keyboard.numpad_keys[9],
        "f1":             keyboard.function_keys[1],
        "f2":             keyboard.function_keys[2],
        "f3":             keyboard.function_keys[3],
        "f4":             keyboard.function_keys[4],
        "f5":             keyboard.function_keys[5],
        "f6":             keyboard.function_keys[6],
        "f7":             keyboard.function_keys[7],
        "f8":             keyboard.function_keys[8],
        "f9":             keyboard.function_keys[9],
        "f10":            keyboard.function_keys[10],
        "f11":            keyboard.function_keys[11],
        "f12":            keyboard.function_keys[12],
        "f13":            keyboard.function_keys[13],
        "f14":            keyboard.function_keys[14],
        "f15":            keyboard.function_keys[15],
        "f16":            keyboard.function_keys[16],
        "f17":            keyboard.function_keys[17],
        "f18":            keyboard.function_keys[18],
        "f19":            keyboard.function_keys[19],
        "f20":            keyboard.function_keys[20],
        "f21":            keyboard.function_keys[21],
        "f22":            keyboard.function_keys[22],
        "f23":            keyboard.function_keys[23],
        "f24":            keyboard.function_keys[24],
        "volumeup":       keyboard.volume_up_key,
        "volup":          keyboard.volume_up_key,
        "volumedown":     keyboard.volume_down_key,
        "voldown":        keyboard.volume_down_key,
        "volumemute":     keyboard.volume_mute_key,
        "volmute":        keyboard.volume_mute_key,
        "tracknext":      keyboard.media_next_track_key,
        "trackprev":      keyboard.media_prev_track_key,
        "playpause":      keyboard.media_play_pause_key,
        "browserback":    keyboard.browser_back_key,
        "browserforward": keyboard.browser_forward_key,
    }

    key_mapping.update(typeables)

    return key_mapping


k = KeyboardWrapper(PyKeyboard())


def keys(spec):
    def handler(node):
        capture_values = {k: v[0].value for k, v in node.by_name.items()}
        formatted_specification = spec.format(**capture_values)

        def action():
            k.keys(formatted_specification)

        return action

    return handler


def press_keys(spec):
    k.keys(spec)


def type_string(s):
    k.keyboard.type_string(s)


def main():
    keys('c-c, h, e, l, l, o')


if __name__ == '__main__':
    main()
