import asyncio
import websockets
import aiohttp.web
import json
import time
import random
from user_manager import UserManager

SERVER_VERSION = "1.1-SNAPSHOT"

users = { }
gateways = []
message_history = [ ]

class User:
    def __init__(self, ws, username):
        self.ws = ws
        self.username = username

class Message:
    def __init__(self, username, message, timestamp):
        self.username = username
        self.message = message
        self.timestamp = timestamp
    
    def to_json_dict(self):
        return {
            "username": self.username,
            "message": self.message,
            "timestamp": self.timestamp,
        }

def html_safe(msg):
    return msg.replace("&", '&amp;').replace("<", '&lt;').replace(">", '&gt;').replace('"', '&quot;')

async def append_message(username, content, timestamp):
    message = Message(username, content, timestamp)
    message_history.insert(0, message)
    while len(message_history) > 100:
        del message_history[-1]
    await broadcast_message(message)

async def broadcast_message(message):
    for user in users:
        await users[user].ws.send_json({ "type": "message", "message": message.to_json_dict() })

async def get_gateway_handler(request):
    try:
        token = request.query['username']
    except KeyError:
        return aiohttp.web.json_response({
            "error": True,
            "message": "Please specify an access token!",
        }, headers={
            "Access-Control-Allow-Origin": "*"
        })
    if not token:
        return aiohttp.web.json_response({
            "error": True,
            "message": "Please specify an access token!",
        }, headers={
            "Access-Control-Allow-Origin": "*"
        })

    manager = UserManager("users.db")
    await manager.connect()
    username = await manager.check_token(token)
    if not username:
        return aiohttp.web.HTTPNotFound()

    if token in users.keys():
        return aiohttp.web.json_response({
            "error": True,
            "message": "Already logged in!",
        }, headers={
            "Access-Control-Allow-Origin": "*"
        })
    
    gwId = str(random.randint(0, 1000))
    while gwId in gateways:
        gwId = str(random.randint(0, 1000))
    gateways.append(gwId)
    await manager.shutdown()

    print(f"User {username} (token: {token}) has been given gateway: {gwId}!")
    return aiohttp.web.json_response({
        "error": False,
        "gatewayId": gwId,
        "username": username
    }, headers={
        "Access-Control-Allow-Origin": "*"
    })

async def ws_handler(request):
    gwId = request.match_info['id']
    print("Got connection to gateway ID: " + gwId)
    if gwId not in gateways:
        return aiohttp.web.HTTPNotFound()
    gateways.remove(gwId)
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    try:
        await message_server(ws, None)
    except Exception as e:
        await ws.close()

async def testing_gateway(request):
    print("Got testing gateway connection!")
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    await message_server(ws, None)

async def message_server(ws, pth):
    #print(f"New connection from: {ws.remote_address}")

    state = 'handshake'
    username = ""
    user = None
    try:
        while True:
            try:
                res = await ws.receive_json()
            except TypeError:
                break
            #if not isinstance(data, str):
            #    await ws.close(1002, 'Invalid data, bytes are not allowed!')
            #    break

            # print(f"recv => {res}")

            if state == 'handshake':
                req = res['cmd']
                if req == 'login':
                    token = html_safe(res['username'])
                    
                    if len(token) != 4:
                        await ws.close(1003, 'Invalid token!')
                        break
                    
                    user_man = UserManager("users.db")
                    await user_man.connect()
                    username = await user_man.check_token(token)
                    await user_man.shutdown()

                    if username is None:
                        await ws.close(1003, 'Invalid token!')
                        break
                    elif username in users:
                        await ws.close(1003, 'Already logged in!')
                        break
                    else:
                        user = User(ws, username)
                        users[username] = user
                        state = 'loggedin'
                        with open("motd.txt") as f:
                            response = {
                                "type": "login",
                                "username": username,
                                "version": SERVER_VERSION,
                                "messageHistory": list(map(lambda m: m.to_json_dict(), message_history)),
                                "motd": f.read().replace("{username}", username),
                            }
                        # print(f"send <= {response}")
                        await ws.send_json(response)
                        await append_message("SYSTEM", f"{username} joined the chat!", time.time())
                        print(f"User {username} has connected and logged in!")
            elif state == 'loggedin':
                req = res['cmd']
                if req == 'message':
                    msg = html_safe(res['message'])
                    if len(msg) == 0:
                        continue
                    print(f'Message: \'{msg}\' from {username}')
                    await append_message(username, msg, time.time())
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed!")
    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed!")
    finally:
        if state == 'loggedin' and user is not None:
            del users[user.username]

print("Starting server...")

app = aiohttp.web.Application()
# server = websockets.serve(message_server, '127.0.0.1', 8000)
app.add_routes([
    aiohttp.web.get("/gateways/{id}", ws_handler),
    aiohttp.web.get("/gateway", get_gateway_handler),
#    aiohttp.web.get("/tgateway", testing_gateway),
])
aiohttp.web.run_app(app)
