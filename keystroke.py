import re
from collections import namedtuple

r = re.compile(r"""(?ixs)
^
(?P<modifiers>
([csaw]-)*
)

(?P<key> [^:/]+)

(
    (/ (?P<inner> \d+))?
    (: (?P<repeat> \d+))
|
    (: (?P<direction> up|down))
)?

(/ (?P<outer> \d+))?
$
""")

Keystroke = namedtuple('Keystroke',
                       ('modifiers',
                        'key',
                        'inner',
                        'repeat',
                        'outer',
                        'direction'))


def parse_keystroke(spec):
    m = r.match(spec).groupdict()

    modifiers = set(m['modifiers'].replace('-', ''))
    key = m['key']

    inner = m['inner']
    if inner is None:
        inner = '0'
    inner = int(inner)

    repeat = m['repeat']
    if repeat is None:
        repeat = '1'
    repeat = int(repeat)

    outer = m['outer']
    if outer is None:
        outer = '0'
    outer = int(outer)

    direction = m['direction']

    return Keystroke(modifiers, key, inner, repeat, outer, direction)
