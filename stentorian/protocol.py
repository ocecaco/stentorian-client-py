import json
import threading
from queue import Queue


class Promise(object):
    def __init__(self):
        self._value = None
        self._event = threading.Event()

    def resolve(self, value):
        self._value = value
        self._event.set()

    def wait(self):
        self._event.wait()
        return self._value


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
        self.notifications = Queue()

        self.lock = threading.Lock()
        self.pending_calls = {}
        self.id_counter = 0

        self.worker_thread = threading.Thread(
            target=self._receive_worker, daemon=True)
        self.worker_thread.start()

    def _receive_worker(self):
        while True:
            done = self._process_incoming()
            if done:
                return

    def _process_incoming(self):
        msg = self.transport.receive()
        if msg is None:
            return True
        obj = json.loads(msg)

        if 'id' not in obj:
            # it's a notification
            self.notifications.put((obj['method'], obj['params']))
        else:
            msg_id = obj['id']

            with self.lock:
                self.pending_calls.pop(msg_id).resolve(obj)

        return False

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

        promise = Promise()

        with self.lock:
            self.pending_calls[msg_id] = promise

        self.transport.send(msg)

        response = promise.wait()

        if 'result' in response:
            return response['result']
        else:
            e = response['error']
            raise RemoteError(code=e['code'],
                              message=e['message'],
                              data=e.get('data'))

    def get_notification(self):
        return self.notifications.get()
