#!/usr/bin/env python3
import os
import ssl
import socket
import capnp
import rpc_capnp
import threading
from hashlib import blake2b
import json
import base64
from queue import Queue

FLASK_SECRET = os.environ['FLASK_SECRET']
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

CLIENTS = {}
CLIENTS_LOCK = threading.Lock()

def handle_client(conn, addr):
    print('got connection from', addr)
    with conn.makefile(mode='rw', encoding='utf-8') as f:
        print('asking for creds')
        f.write(json.dumps({ 'command': ['get_property', 'script-opts'] })+'\n')
        f.flush()
        resp = json.loads(f.readline())
        print('resp:', resp)
        token = resp['data']['token'].split('@')
        user_id = token[0]
        digest = base64.b64decode(token[1])
        h = blake2b(key=FLASK_SECRET.encode('utf-8'), digest_size=18)
        h.update(user_id.encode('utf-8'))
        if h.digest() != digest:
            print('bad auth')
            f.write('bad auth')
            return
        print('good auth')
        q = Queue()
        with CLIENTS_LOCK:
            CLIENTS[user_id] = q
        while True:
            cmd = q.get()
            print('running', cmd)
            f.write(json.dumps({ 'command': ['loadfile', cmd.loadFile.path] })+'\n')
            f.flush()
            resp = json.loads(f.readline())
            print('resp:', resp)

def run_socket_server():
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    if FLASK_ENV == 'development':
        ctx.load_cert_chain('selfsigned.crt', 'selfsigned.key')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    else:
        ctx.load_cert_chain(
            '/etc/letsencrypt/live/neettv.rje.li/fullchain.pem',
            '/etc/letsencrypt/live/neettv.rje.li/privkey.pem')
        ctx.check_hostname = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 8443))
        sock.listen(5)
        with ctx.wrap_socket(sock, server_side=True) as ssock:
            while True:
                conn, addr = ssock.accept()
                t = threading.Thread(target=handle_client, args=(conn, addr))
                t.daemon = True
                t.start()

class RpcServer(rpc_capnp.MpvSockServer.Server):
    def __init__(self):
        pass
    def execute(self, userId, cmd, _context):
        with CLIENTS_LOCK:
            if userId in CLIENTS:
                print('found client')
                CLIENTS[userId].put(cmd)
            else:
                print('client', userId, 'not found')
        return 'none'

if __name__ == '__main__':
    print('starting socket server')
    t = threading.Thread(target=run_socket_server, args=())
    t.daemon = True
    t.start()

    print('running rpc server')
    rpc_server = capnp.TwoPartyServer('localhost:60000', bootstrap=RpcServer())
    rpc_server.run_forever()
