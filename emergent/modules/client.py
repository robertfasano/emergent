import asyncio
import json
import pickle

class Client():
    def __init__(self, addr):
        self.addr = addr
        self.params = self.get_params()
        loop = asyncio.get_event_loop()
        message = {'op': 'connect'}
        state = loop.run_until_complete(self.tcp_echo_client(message, loop))

    def actuate(self, state):
        return self.send({'op': 'actuate', 'params': state})

    def echo(self, message):
        message = {'op': 'echo', 'params': message}
        resp = self.send(message)
        return resp

    def send(self, message):
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.tcp_echo_client(message, loop))
        return response

    async def tcp_echo_client(self, message, loop):
        reader, writer = await asyncio.open_connection(self.addr, 8888,
                                                       loop=loop)
        writer.write(json.dumps(message).encode())
        await writer.drain()
        data = await reader.read()
        writer.close()
        await writer.wait_closed()
        return pickle.loads(data)
        # return json.loads(data.decode())

    def get_state(self):
        return self.send({'op': 'get_state'})

    def get_network(self):
        return self.send({'op': 'get_network'})


    def get_params(self):
        return self.send({'op': 'get_params'})


if __name__ == '__main__':
    c = Client()
