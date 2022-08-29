import json
from aiohttp import web

WS_FILE = 'websocket.html'


def init():
    app = web.Application()
    app['sockets'] = []
    app.add_routes([
        web.get('/', ws_handler),
        web.post('/post', post_handler)
    ])
    app.on_shutdown.append(on_shutdown)
    return app


async def post_handler(request: web.Request):
    data = await request.post()
    for news in json.loads(data['news']):
        for ws in request.app['sockets']:
            await ws.send_str(json.dumps(news))


async def ws_handler(request: web.Request):
    resp = web.WebSocketResponse()
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, 'rb') as fp:
            return web.Response(body=fp.read(), content_type='text/html')

    await resp.prepare(request)

    try:
        request.app['sockets'].append(resp)

        async for msg in resp:
            if msg.data == 'PING':
                await resp.send_str('PONG')
            else:
                return resp
        return resp
    finally:
        request.app['sockets'].remove(resp)


async def on_shutdown(app: web.Application):
    for ws in app['sockets']:
        await ws.close()


web.run_app(init())
