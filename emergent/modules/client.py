import asyncio
import json

class Client():
    def __init__(self):
        return

    async def tcp_echo_client(self, message, loop):
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888,
                                                       loop=loop)
        writer.write(json.dumps(message).encode())
        data = await reader.read(1000)

        writer.close()
        return json.loads(data.decode())

    def get_state(self):
        loop = asyncio.get_event_loop()
        message = {'op': 'get_state'}
        state = loop.run_until_complete(self.tcp_echo_client(message, loop))
        print(state)
        return state
