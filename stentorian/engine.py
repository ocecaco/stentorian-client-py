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


class CommandGrammarControl(object):
    def __init__(self, engine, grammar_id, rules):
        self.grammar_id = grammar_id
        self.engine = engine
        self.rules = rules

    def rule_activate(self, rule):
        self.engine._request('command_grammar_rule_activate',
                             self.grammar_id, rule.name)

    def rule_deactivate(self, rule):
        self.engine._request('command_grammar_rule_deactivate',
                             self.grammar_id, rule.name)

    def rule_activate_all(self):
        for r in self.rules:
            self.rule_activate(r)

    def rule_deactivate_all(self):
        for r in self.rules:
            self.rule_deactivate(r)

    def list_append(self, grammar_list, word):
        self.engine._request('command_grammar_list_append',
                             self.grammar_id, grammar_list.name, word)

    def list_remove(self, grammar_list, word):
        self.engine._request('command_grammar_list_remove',
                             self.grammar_id, grammar_list.name, word)

    def list_clear(self, grammar_list):
        self.engine._request('command_grammar_list_clear',
                             self.grammar_id, grammar_list.name)

    def unload(self):
        self.engine._command_grammar_unload(self.grammar_id)


class SelectGrammarControl(object):
    def __init__(self, engine, grammar_id):
        self.grammar_id = grammar_id
        self.engine = engine

    def activate(self):
        self.engine._request('select_grammar_activate', self.grammar_id)

    def deactivate(self):
        self.engine._request('select_grammar_deactivate', self.grammar_id)

    def text_set(self, text):
        self.engine._request('select_grammar_text_set', self.grammar_id, text)

    def text_get(self):
        return self.engine._request('select_grammar_text_get', self.grammar_id)

    def text_change(self, start, stop, text):
        self.engine._request('select_grammar_text_change',
                             self.grammar_id, start, stop, text)

    def text_insert(self, start, text):
        self.engine._request('select_grammar_text_insert',
                             self.grammar_id, start, text)

    def text_delete(self, start, stop):
        self.engine._request('select_grammar_text_delete',
                             self.grammar_id, start, stop)

    def unload(self):
        self.engine._select_grammar_unload(self.grammar_id)


class DictationGrammarControl(object):
    def __init__(self, engine, grammar_id):
        self.grammar_id = grammar_id
        self.engine = engine

    def activate(self):
        self.engine._request('dictation_grammar_activate', self.grammar_id)

    def deactivate(self):
        self.engine._request('dictation_grammar_deactivate', self.grammar_id)

    def context(self, text):
        self.engine._request(
            'dictation_grammar_context_set', self.grammar_id, text)

    def unload(self):
        self.engine._dictation_grammar_unload(self.grammar_id)


class CatchallGrammarControl(object):
    def __init__(self, engine, grammar_id):
        self.grammar_id = grammar_id
        self.engine = engine

    def activate(self):
        self.engine._request('catchall_grammar_activate', self.grammar_id)

    def deactivate(self):
        self.engine._request('catchall_grammar_deactivate', self.grammar_id)

    def unload(self):
        self.engine._catchall_grammar_unload(self.grammar_id)


class EngineRegistration(object):
    def __init__(self, engine_id, engine):
        self.engine_id = engine_id
        self.engine = engine

    def unregister(self):
        self.engine._engine_unregister(self.engine_id)


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


class CallbackManager(object):
    def __init__(self):
        self.callbacks = {}

    def add_callback(self, entity_id, cb):
        self.callbacks[entity_id] = cb

    def remove_callback(self, entity_id):
        del self.callbacks[entity_id]

    def handle_callback(self, entity_id, event):
        self.callbacks[entity_id](event)


class Engine(object):
    def __init__(self, client):
        self.client = client
        self.client.notification_handler = self._receive_notification

        self.command_grammars = CallbackManager()
        self.select_grammars = CallbackManager()
        self.dictation_grammars = CallbackManager()
        self.catchall_grammars = CallbackManager()
        self.engine_registrations = CallbackManager()

        self.managers = {
            "command_grammar_notification": self.command_grammars,
            "select_grammar_notification": self.select_grammars,
            "dictation_grammar_notification": self.dictation_grammars,
            "catchall_grammar_notification": self.catchall_grammars,
            "engine_notification": self.engine_registrations,
        }

    def _request(self, *args, **kwargs):
        return self.client.request(*args, **kwargs)

    def _receive_notification(self, method, params):
        cb_manager = self.managers[method]
        entity_id, event = params
        cb_manager.handle_callback(entity_id, event)

    def register(self, callback):
        e = self.client.request('engine_register')
        self.engine_registrations.add_callback(e, callback)
        return EngineRegistration(e, self.client, self.engine_registrations)

    def command_grammar_load(self, grammar, callback):
        g = self.client.request('command_grammar_load', grammar.serialize())
        self.command_grammars.add_callback(g, callback)
        rule_names = [r for r in grammar.rules if r.exported]
        return CommandGrammarControl(self, g, rule_names)

    def _command_grammar_unload(self, grammar_id):
        self.client.request('command_grammar_unload', grammar_id)
        self.command_grammars.remove_callback(grammar_id)

    def select_grammar_load(self, select_words, through_words, callback):
        g = self.client.request('select_grammar_load',
                                select_words, through_words)
        self.select_grammars.add_callback(g, callback)
        return SelectGrammarControl(self, g)

    def _select_grammar_unload(self, grammar_id):
        self.client.request('select_grammar_unload', grammar_id)
        self.select_grammars.remove_callback(grammar_id)

    def dictation_grammar_load(self, callback):
        g = self.client.request('dictation_grammar_load')
        self.dictation_grammars.add_callback(g, callback)
        return DictationGrammarControl(self, g)

    def _dictation_grammar_unload(self, grammar_id):
        self.client.request('dictation_grammar_unload', grammar_id)
        self.dictation_grammars.remove_callback(grammar_id)

    def catchall_grammar_load(self, callback):
        g = self.client.request('catchall_grammar_load')
        self.catchall_grammar.add_callback(g, callback)
        return CatchallGrammarControl(self, g)

    def _catchall_grammar_unload(self, grammar_id):
        self.client.request('catchall_grammar_unload', grammar_id)
        self.catchall_grammars.remove_callback(grammar_id)

    def microphone_set_state(self, state):
        self.client.request('microphone_set_state', state)

    def microphone_get_state(self):
        return self.client.request('microphone_get_state')

    def get_current_user(self):
        return self.client.request('get_current_user')

    def process_notifications(self):
        self.client.process_notifications()
