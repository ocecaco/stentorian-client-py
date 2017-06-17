import elementparser
from grammar import Capture, Alternative


class ActionCallback(object):
    def __init__(self, semantics):
        self.semantics = semantics

    def phrase_start(self):
        pass

    def phrase_recognition_failure(self):
        pass

    def phrase_finish(self, foreign, words, parse):
        if not foreign:
            v = self.semantics.evaluate(parse)
            print(v)


capture_counter = 1


def new_capture_name():
    global capture_counter
    name = '@@capture{}'.format(capture_counter)
    capture_counter += 1
    return name


def choice(semantics, options):
    new_options = {k: (lambda n, c, v=v: v) for k, v in options.items()}
    return mapping(semantics, new_options)


def action(semantics, element, handler):
    name = new_capture_name()
    semantics.handler(name, handler)
    return Capture(name, element)


def mapping(semantics, options):
    branches = []
    for k, v in options.items():
        child = elementparser.parse(k)
        branches.append(action(semantics, child, v))

    return Alternative(branches)
