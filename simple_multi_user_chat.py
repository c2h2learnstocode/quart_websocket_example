from quart import Quart, render_template, websocket
from functools import partial, wraps
import asyncio
import json
import time
from datetime import datetime

app = Quart(__name__)

connected_websockets = set()

beacon_start=False


async def beacon_json():
    a={}
    while True:
        await asyncio.sleep(5)
        dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        a["beacon"]=dt_string
        a["connected_websockets"]=len(connected_websockets)
        await broadcast(json.dumps(a))

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
    #beaconer = asyncio.create_task(beacon_json())
    await asyncio.gather(producer, consumer)

@app.before_serving
async def startup():
    app.beacon_task = asyncio.create_task(beacon_json())

@app.after_serving
async def shutdown():
    app.beacon_task.cancel()

if __name__ == '__main__':
    app.run(port=5000)
