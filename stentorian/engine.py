from contextlib import contextmanager
import socket
import time
import functools
import logging

from .protocol import LineProtocolClient, JsonRpcClient


logger = logging.getLogger(__name__)


def retry(exc, delay, tries, log):
    def do_decorate(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for _ in range(tries - 1):
                start = time.time()
                try:
                    return f(*args, **kwargs)
                except exc:
                    elapsed = time.time() - start
                    remaining = delay - elapsed
                    if remaining > 0:
                        time.sleep(remaining)
                    log.debug('call failed, retrying...', exc_info=True)

            return f(*args, **kwargs)

        return wrapper

    return do_decorate


@retry(OSError, delay=3, tries=100, log=logger)
def _connect_socket(host, port, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(timeout)
        s.connect((host, port))
        s.settimeout(None)
        return s
    except:
        s.close()
        raise


def wait_for_user(engine):
    while engine.get_current_user() is None:
        logger.debug('get_current_user returned None, retrying...')
        time.sleep(1)


@contextmanager
def connect(host, port):
    logger.info('attempting to connect to server')
    s = _connect_socket(host, port, timeout=2)
    logger.info('successfully connected to server')
    try:
        proto = LineProtocolClient(s)
        client = JsonRpcClient(proto)
        engine = Engine(client)
        logger.info('waiting for user profile to be selected')
        wait_for_user(engine)
        logger.info('user profile selected')
        yield engine
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()


class GrammarControl(object):
    def __init__(self, grammar_id, engine, rule_names):
        self.grammar_id = grammar_id
        self.client = engine.client
        self.engine = engine
        self.rule_names = rule_names

    def rule_activate(self, rule):
        self.client.request('grammar_rule_activate', self.grammar_id,
                            rule.name)

    def rule_deactivate(self, rule):
        self.client.request('grammar_rule_deactivate', self.grammar_id,
                            rule.name)

    def rule_activate_all(self):
        for r in self.rule_names:
            self.client.request('grammar_rule_activate', self.grammar_id, r)

    def rule_deactivate_all(self):
        for r in self.rule_names:
            self.client.request('grammar_rule_deactivate', self.grammar_id, r)

    def list_append(self, grammar_list, word):
        self.client.request('grammar_list_append', self.grammar_id,
                            grammar_list.name, word)

    def list_remove(self, grammar_list, word):
        self.client.request('grammar_list_remove', self.grammar_id,
                            grammar_list.name, word)

    def list_clear(self, grammar_list):
        self.client.request('grammar_list_clear', self.grammar_id,
                            grammar_list.name)

    def unload(self):
        if self.grammar_id is None:
            return

        self.engine._unregister_grammar_callback(
            self.grammar_id)  # pylint: disable=protected-access
        self.client.request('grammar_unload', self.grammar_id)
        self.grammar_id = None


class EngineRegistration(object):
    def __init__(self, engine_id, engine):
        self.engine_id = engine_id
        self.client = engine.client
        self.engine = engine

    def unregister(self):
        if self.engine_id is None:
            return

        self.engine._unregister_engine_callback(
            self.engine_id)  # pylint: disable=protected-access
        self.client.request('engine_unregister', self.engine_id)
        self.engine_id = None


class ParseTree(object):
    def __init__(self, all_words, data):
        self.name = data['name']
        self._slice = data['slice']
        self._all_words = all_words
        self.children = [ParseTree(all_words, c) for c in data['children']]

    @property
    def words(self):
        start, stop = self._slice
        return self._all_words[start:stop]

    def _pretty_lines(self, last):
        yield "+-- " + self.name + " -> " + str(self.words)

        indent = '|   ' if not last else '    '

        for i, c in enumerate(self.children):
            child_last = (i == len(self.children) - 1)
            for line in c._pretty_lines(child_last):  # pylint: disable=protected-access
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
            if not foreign:
                tree = ParseTree(words, parse)
                assert tree.name == '__top'
                assert len(tree.children) == 1
                handler.phrase_finish(tree.children[0])
            else:
                handler.phrase_finish_foreign(words)

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
        rule_names = [r.name for r in grammar.rules if r.exported]
        return GrammarControl(g, self, rule_names)

    def _unregister_grammar_callback(self, grammar_id):
        del self.grammar_callbacks[grammar_id]

    def microphone_set_state(self, state):
        self.client.request('microphone_set_state', state)

    def microphone_get_state(self):
        return self.client.request('microphone_get_state')

    def get_current_user(self):
        return self.client.request('get_current_user')

    def process_notifications(self):
        self.client.process_notifications()
