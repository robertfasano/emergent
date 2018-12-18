import asyncio
import json
from emergent.modules import Hub
from threading import Thread
import logging as log
class Server():
    ''' Allows decentralized data viewing via asynchronous communications between the EMERGENT
        master and a remote client. '''
    def __init__(self):
        ''' Sets up a new thread for serving. '''
        self.loop = asyncio.get_event_loop()
        coro = asyncio.start_server(self.handle_command, '127.0.0.1', 8888, loop=self.loop)
        self.server = self.loop.run_until_complete(coro)
        log.info('Serving on {}'.format(self.server.sockets[0].getsockname()))
        thread = Thread(target=self.start)
        thread.start()

    def start(self):
        self.loop.run_forever()

    def get_state(self):
        state = {}
        for c in Hub.instances:
            state[c.name] = c.state
        return state

    async def send_context(self, reader, writer):
        ''' When a command is received from a client, respond with the current state '''
        resp = json.dumps(self.get_state()).encode()
        writer.write(resp)
        await writer.drain()
        writer.close()

    async def handle_command(self, reader, writer):
        data = await reader.read(100)
        addr = writer.get_extra_info('peername')

        message = json.loads(data.decode())
        print(message)
        op = message['op']
        if op == 'get_state':
            await self.send_context(reader, writer)
