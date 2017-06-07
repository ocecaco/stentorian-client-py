import socket
import json
from collections import deque


class LineProtocolClient(object):
    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        self.buf = b''

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def send(self, message):
        message = message.encode('utf-8') + b'\n'
        self.socket.sendall(message)

    def receive(self):
        while b'\n' not in self.buf:
            data = self.socket.recv(4096)

            if not data:
                return None

            self.buf += data

        msg, rest = self.buf.split(b'\n', 1)
        self.buf = rest

        return msg.decode('utf-8')


class JsonRpcClient(object):
    def __init__(self, transport, notification_handler):
        self.transport = transport
        self.notification_handler = notification_handler

        self.notifications = deque()
        self.id_counter = 0

    def __del__(self):
        self.transport.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.transport.close()

    def _wait_for_response(self, msg_id):
        # get the first message that isn't a notification
        obj = None
        while obj is None:
            obj = self._get_message()

        assert(msg_id == obj['id'])
        return obj

    def _get_message(self):
        msg = self.transport.receive()
        obj = json.loads(msg)

        if 'id' not in obj:
            # it's a notification
            self.notifications.append(obj)
            return None
        else:
            return obj

    def _perform_call(self, method, *args, **kwargs):
        self.id_counter += 1

        assert(not args or not kwargs)

        msg_id = self.id_counter

        call = {
            "jsonrpc": "2.0",
            "method": method,
            "params": args or kwargs,
            "id": msg_id,
        }

        msg = json.dumps(call)

        self.transport.send(msg)
        response = self._wait_for_response(msg_id)

        return response['result']

    def __getattr__(self, name):
        def caller(*args, **kwargs):
            return self._perform_call(name, *args, **kwargs)

        return caller

    def _wait_for_notification(self):
        if not self.notifications:
            obj = self._get_message()
            assert(obj is None)

        n = self.notifications.popleft()
        return n

    def process_notification(self):
        n = self._wait_for_notification()
        h = getattr(self.notification_handler, n['method'])
        p = n['params']

        h(*p)


def jsonrpc(host, port, notification_handler):
    return JsonRpcClient(LineProtocolClient(host, port),
                         notification_handler)


def build_action(tree, callback):
    child_actions = [build_action(c, callback) for c in tree['children']]
    return callback(tree, child_actions)


class NotificationHandler(object):
    def grammar_notification(self, grammar_id, event):
        if event['type'] == 'phrase_finish':
            print(' '.join(event['words']))
            print(event['parse'])

    def engine_notification(self, engine_id, event):
        pass


def main():
    with jsonrpc('127.0.0.1', 1337, NotificationHandler()) as c:
        print(c.microphone_set_state('sleeping'))
        print(c.microphone_get_state())
        print(c.engine_register())
        grammar = {'children': [{'type': 'word', 'text': 'my'}, {'type': 'word', 'text': 'grammar'}, {'type': 'word', 'text': 'press'}, {'child': {'child': {'children': [{'type': 'word', 'text': 'mint'}, {'type': 'word', 'text': 'soap'}], 'type': 'alternative'}, 'type': 'repetition'}, 'type': 'capture', 'name': 'keys'}], 'type': 'sequence'}
        g = c.grammar_load({"rules": [{"name": "testing", "exported": True, "definition": grammar}]}, False)
        print(c.grammar_rule_activate(g, 'testing'))

        while True:
            c.process_notification()


if __name__ == '__main__':
    main()
