from quart import Quart, render_template, websocket
from functools import partial, wraps
import asyncio

app = Quart(__name__)

connected_websockets = set()

def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        queue = asyncio.Queue()
        connected_websockets.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            connected_websockets.remove(queue)
    return wrapper

async def broadcast(message):
    for queue in connected_websockets:
        await queue.put(message)

@app.route('/')
async def index():
    return await render_template('index.html')


async def sending(queue):
    while True:
        data = await queue.get()
        await websocket.send(data)

async def receiving():
    while True:
        data = await websocket.receive()
        await broadcast(data)

@app.websocket('/ws0')
@collect_websocket
async def ws(queue):
    producer = asyncio.create_task(sending(queue))
    consumer = asyncio.create_task(receiving())
    await asyncio.gather(producer, consumer)

if __name__ == '__main__':
    app.run(port=5000)
