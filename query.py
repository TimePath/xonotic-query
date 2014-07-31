#!/usr/bin/env python
__author__ = 'TimePath'

import random
import socket
import time
from threading import Thread


class Utils:
    def chunks(l, n):
        """
        Yield successive n-sized chunks from l.
        """
        for i in range(0, len(l), n):
            yield l[i:i + n]


class BaseConnection:
    header = b'\xff' * 4

    def connect(self, server):
        self.server = server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect(self.server)

    def send(self, payload):
        self.sock.send(self.header + bytes(payload, 'utf-8'))

    def recv(self):
        return self.sock.recv(2048)

    def __del__(self):
        self.sock.close()
        del self.sock


class MasterConnection(BaseConnection):
    def __init__(self):
        self.connect(random.choice([
            ("ghdigital.com", 27950),
            ("dpmaster.deathmask.net", 27950),
            ("dpmaster.tchr.no", 27950)
        ]))

    def query(self):
        self.send('getservers Xonotic 3 empty full')

        serverResponse = self.recv()
        serverBytes = serverResponse[len(self.header) + len('getserversResponse'):]
        return (self.parse(x[1:]) for x in Utils.chunks(serverBytes, 7))

    @staticmethod
    def parse(buf):
        A = buf[0] & 0xff

        B = buf[1] & 0xff
        C = buf[2] & 0xff
        D = buf[3] & 0xff
        port = buf[4] & 0xff
        port <<= 8
        port |= buf[5] & 0xff
        address = "%s.%s.%s.%s" % (A, B, C, D)
        return (address, port)


class ServerConnection(BaseConnection):
    def __init__(self, server):
        self.connect(server)

    def getstatus(self):
        self.send('getstatus')

        serverResponse = self.recv()
        serverBytes = serverResponse[len(self.header) + len('statusResponse'):].strip()
        ls = str(serverBytes, 'utf-8').split('\\')[1:]
        ret = {}
        it = iter(ls)
        for x in it:
            ret[x] = next(it)
        temp = ret['d0_blind_id'].split('\n')
        tempServer = temp[0].split(' ', 1)
        server = {'encryption': bool(int(tempServer[0]))}
        if server['encryption'] and len(tempServer) > 1:
            tempServerAuth = tempServer[1].split('@')
            server['key'] = tempServerAuth[0]
            server['id'] = tempServerAuth[1]
        del ret['d0_blind_id']
        ret['server'] = server
        ret['clients'] = [(player[2], dict(score=player[0], ping=player[1])) for player in (token.split(' ', 2) for token in temp[1:])]
        return ret

if __name__ == '__main__':
    m = MasterConnection()
    servers = m.query()
    for server in servers:
        def go():
            try:
                status = ServerConnection(server).getstatus()
                print(server)
                print(status)
            except ConnectionRefusedError: pass
        Thread(target=go).start()
        time.sleep(0.5)
