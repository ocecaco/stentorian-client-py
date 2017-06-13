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
    def __init__(self, grammar_id, client):
        self.grammar_id = grammar_id
        self.client = client

    def rule_activate(self, name):
        self.client.request('grammar_rule_activate', self.grammar_id, name)


class ParseTree(object):
    def __init__(self, all_words, json):
        self.name = json['name']
        self._slice = json['slice']
        self._all_words = all_words
        self.children = [ParseTree(all_words, c) for c in json['children']]

    @property
    def words(self):
        start, stop = self._slice
        return self._all_words[start:stop]

    def child_by_name(self, name, ty=None):
        for i, c in enumerate(self.children):
            if c.name == name:
                return i, c

        return KeyError('child with name "{}" not found', name)


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
        pass

    def _receive_notification(self, method, params):
        object_id, event = params
        method_mapping = {
            'grammar_notification': self._grammar_notification,
            'engine_notification': self._engine_notification,
        }
        handler = method_mapping[method]
        handler(object_id, event)

    def grammar_load(self, grammar, callback, foreign=False):
        g = self.client.request('grammar_load', grammar.serialize(), foreign)
        # TODO: unregister callback at the right time
        self.grammar_callbacks[g] = callback
        return GrammarControl(g, self.client)

    def process_notifications(self):
        self.client.process_notifications()
