import json
from collections import deque


class RemoteError(Exception):
    def __init__(self, code, message, data):
        super().__init__(message)

        self.code = code
        self.message = message
        self.data = data


class LineProtocolClient(object):
    def __init__(self, sock):
        self.socket = sock
        self.buf = b''

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
    def __init__(self, transport):
        self.transport = transport
        self.notification_handler = None

        self.notifications = deque()
        self.id_counter = 0

    def _wait_for_response(self, msg_id):
        # get the first message that isn't a notification
        obj = None
        while obj is None:
            obj = self._get_message()

        assert msg_id == obj['id']
        return obj

    def _get_message(self):
        msg = self.transport.receive()
        obj = json.loads(msg)

        if 'id' not in obj:
            # it's a notification
            self.notifications.append(obj)
            return None

        return obj

    def request(self, method, *args, **kwargs):
        self.id_counter += 1

        assert not args or not kwargs

        msg_id = self.id_counter

        call = {
            "jsonrpc": "2.0",
            "method": method,
            "params": kwargs or args,
            "id": msg_id,
        }

        msg = json.dumps(call)

        self.transport.send(msg)
        response = self._wait_for_response(msg_id)

        if 'result' in response:
            return response['result']
        else:
            e = response['error']
            raise RemoteError(code=e['code'],
                              message=e['message'],
                              data=e.get('data'))

    def _wait_for_notification(self):
        if not self.notifications:
            obj = self._get_message()
            assert obj is None

        n = self.notifications.popleft()
        return n

    def process_notifications(self):
        while True:
            n = self._wait_for_notification()
            self.notification_handler(n['method'], n['params']) # pylint: disable=not-callable
