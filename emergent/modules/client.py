import asyncio
import json
import pickle

class Client():
    def __init__(self):
        self.params = self.get_params()
        loop = asyncio.get_event_loop()
        message = {'op': 'connect'}
        state = loop.run_until_complete(self.tcp_echo_client(message, loop))

    def actuate(self, state):
        return self.send({'op': 'actuate', 'params': state})

    def send(self, message):
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.tcp_echo_client(message, loop))
        return response

    async def tcp_echo_client(self, message, loop):
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888,
                                                       loop=loop)
        writer.write(json.dumps(message).encode())
        data = await reader.read(4096)

        writer.close()
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
