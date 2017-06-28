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
    inner = int(m.get('inner', '0'))
    repeat = int(m.get('repeat', '1'))
    outer = int(m.get('outer', '0'))
    direction = m['direction']

    return Keystroke(modifiers, key, inner, repeat, outer, direction)
