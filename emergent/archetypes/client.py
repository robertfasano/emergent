import asyncio
import json

async def tcp_echo_client(message, loop):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888,
                                                   loop=loop)
    writer.write(message.encode())
    data = await reader.read(1000)

    writer.close()
    return json.loads(data.decode())

def get_state():
    loop = asyncio.get_event_loop()
    state = loop.run_until_complete(tcp_echo_client('get_state', loop))
    return state
