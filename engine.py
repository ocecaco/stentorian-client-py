from protocol import LineProtocolClient, JsonRpcClient
from contextlib import contextmanager
import socket


@contextmanager
def connect(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        proto = LineProtocolClient(s)
        client = JsonRpcClient(proto)
        engine = Engine(client)
        yield engine
    finally:
        s.close()


class GrammarControl(object):
    def __init__(self, grammar_id, engine):
        self.grammar_id = grammar_id
        self.client = engine.client
        self.engine = engine

    def __del__(self):
        try:
            self.unload()
        except OSError:
            pass

    def rule_activate(self, name):
        self.client.request('grammar_rule_activate', self.grammar_id, name)

    def rule_deactivate(self, name):
        self.client.request('grammar_rule_deactivate', self.grammar_id, name)

    def list_append(self, name, word):
        self.client.request('grammar_list_append', self.grammar_id, name, word)

    def list_remove(self, name, word):
        self.client.request('grammar_list_remove', self.grammar_id, name, word)

    def list_clear(self, name):
        self.client.request('grammar_list_clear', self.grammar_id, name)

    def unload(self):
        if self.grammar_id is None:
            return

        self.engine._unregister_grammar_callback(self.grammar_id)
        self.client.request('grammar_unload', self.grammar_id)
        self.grammar_id = None


class EngineRegistration(object):
    def __init__(self, engine_id, engine):
        self.engine_id = engine_id
        self.client = engine.client
        self.engine = engine

    def __del__(self):
        try:
            self.unregister()
        except OSError:
            pass

    def unregister(self):
        if self.engine_id is None:
            return

        self.engine._unregister_engine_callback(self.engine_id)
        self.client.request('engine_unregister', self.engine_id)
        self.engine_id = None


class ParseTree(object):
    def __init__(self, all_words, json):
        self.rule = json['rule']
        self.name = json['name']
        self._slice = json['slice']
        self._all_words = all_words
        self.children = [ParseTree(all_words, c) for c in json['children']]

    @property
    def words(self):
        start, stop = self._slice
        return self._all_words[start:stop]

    def child_by_name(self, name):
        for c in self.children:
            if c.name == name:
                return c

        return None

    def _pretty_lines(self, last):
        yield "+-- " + self.name + " -> " + str(self.words)

        indent = '|   ' if not last else '    '

        for i, c in enumerate(self.children):
            child_last = (i == len(self.children) - 1)
            for line in c._pretty_lines(child_last):
                yield indent + line

    def pretty(self):
        return '\n'.join(self._pretty_lines(True))


class Engine(object):
    def __init__(self, client):
        self.client = client
        self.client.notification_handler = self._receive_notification

        self.grammar_callbacks = {}
        self.engine_callbacks = {}

    def _grammar_notification(self, grammar_id, event):
        handler = self.grammar_callbacks[grammar_id]

        t = event['type']
        if t == 'phrase_start':
            handler.phrase_start()
        elif t == 'phrase_recognition_failure':
            handler.phrase_recognition_failure()
        elif t == 'phrase_finish':
            foreign = event['foreign_grammar']
            words = event['words']
            parse = event['parse']
            tree = ParseTree(words, parse) if not foreign else None
            handler.phrase_finish(foreign, words, tree)

    def _engine_notification(self, engine_id, event):
        handler = self.engine_callbacks[engine_id]

        t = event['type']
        if t == 'paused':
            handler.paused()
        elif t == 'microphone_state_changed':
            state = event['state']
            handler.microphone_state_changed(state)

    def _receive_notification(self, method, params):
        object_id, event = params
        method_mapping = {
            'grammar_notification': self._grammar_notification,
            'engine_notification': self._engine_notification,
        }
        handler = method_mapping[method]
        handler(object_id, event)

    def register(self, callback):
        e = self.client.request('engine_register')
        self.engine_callbacks[e] = callback
        return EngineRegistration(e, self)

    def _unregister_engine_callback(self, engine_id):
        del self.engine_callbacks[engine_id]

    def grammar_load(self, grammar, callback, foreign=False):
        g = self.client.request('grammar_load', grammar.serialize(), foreign)
        self.grammar_callbacks[g] = callback
        return GrammarControl(g, self)

    def _unregister_grammar_callback(self, grammar_id):
        del self.grammar_callbacks[grammar_id]

    def microphone_set_state(self, state):
        self.client.request('microphone_set_state', state)

    def microphone_get_state(self):
        return self.client.request('microphone_get_state')

    def process_notifications(self):
        self.client.process_notifications()
