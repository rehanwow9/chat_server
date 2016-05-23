import sys
import random

from twisted.web.static import File
from twisted.python import log
from twisted.web.server import Site
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol

from autobahn.twisted.resource import WebSocketResource


class SomeServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        """
        Connection from client is opened. Fires after opening
        websockets handshake has been completed and we can send
        and receive messages.

        Register client in factory, so that it is able to track it.
        Try to find conversation partner for this client.
        """
        self.factory.register(self)
        self.factory.giveInfo(self)

    def connectionLost(self, reason):
        """
        Client lost connection, either disconnected or some error.
        Remove client from list of tracked connections.
        """
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        """
        Message sent from client, communicate this message to its conversation partner,
        """
        self.factory.communicate(self, payload, isBinary)


import datetime
class ClientModel(object):
    """docstring for ClientModel"""
    def __init__(self, client):
        self.client = client
        self.lastMessageTime = datetime.datetime.now()
        self.lastMessage = ""

    def updateLastMessage(self, msg):
        self.lastMessage = msg
        self.lastMessageTime = datetime.datetime.now()

    def isDuplicate(self, msg):
        return (self.lastMessage == msg) and ((datetime.datetime.now() - self.lastMessageTime).seconds < 5)

class ChatRouletteFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(ChatRouletteFactory, self).__init__(*args, **kwargs)
        self.clients = {}
        self.peerToDestinationMap = {}
        self.currID = 100000000

    def register(self, client):
        """
        Add client to list of managed connections.
        """
        destinationId = self.currID
        self.currID += 1
        self.clients[destinationId] = ClientModel(client)
        self.peerToDestinationMap[client.peer] = destinationId

    def unregister(self, client):
        """
        Remove client from list of managed connections.
        """
        self.clients.pop(self.peerToDestinationMap[client.peer])
        self.peerToDestinationMap.pop(client.peer)

    def giveInfo(self, client):
        """
        Echoes info of the socket server.
        Client device ID
        List of IDs of connected devices
        """
        deviceIDMsg = "Your ID: " + str(self.peerToDestinationMap[client.peer])
        deviceListMsg = "Connected Devices: \n" + str(self.peerToDestinationMap.values())
        chatUsageMsg = "Chat usage: send,destinationId,msg"
        retMsg = deviceIDMsg + "\n" + deviceListMsg + "\n" + chatUsageMsg
        client.sendMessage(retMsg.encode('utf8'))

    def communicate(self, client, payload, isBinary):
        """
        Broker message from client to its partner.
        """
        # print(payload.decode('utf-8'))
        strPayload = payload.decode('utf-8')
        if (strPayload == "help"):
            self.giveInfo(client)
        else:
            try:
                cmd = strPayload.split(',')[0].strip()
                destinationId = int(strPayload.split(',')[1].strip())
                msg = str(self.peerToDestinationMap[client.peer]) + ":" + strPayload.split(',')[2]

                if cmd == "send":
                    if destinationId in self.peerToDestinationMap.values():
                        #import pdb; pdb.set_trace()
                        if self.clients[(self.peerToDestinationMap[client.peer])].isDuplicate(msg) is False:
                            self.clients[destinationId].client.sendMessage(msg.encode('utf8'))
                            self.clients[(self.peerToDestinationMap[client.peer])].updateLastMessage(msg)
                        else:
                            client.sendMessage("Duplicate message".encode('utf8'))
                    else:
                        client.sendMessage("Invalid destinationId".encode('utf8'))
                else:
                    client.sendMessage("Invalid Command".encode('utf8'))
            except Exception as e:
                client.sendMessage("Error reading the command".encode('utf8'))

        # if not c["partner"]:
        #     c["object"].sendMessage("Sorry you dont have partner yet, check back in a minute".encode('utf8'))
        # else:
        #     c["partner"].sendMessage(payload)

from configparser import ConfigParser
if __name__ == "__main__":
    log.startLogging(sys.stdout)
    config = ConfigParser()
    config.read('server.cfg')
    port = config.getint('Settings', 'port')

    factory = ChatRouletteFactory(u"ws://localhost:{}".format(port))
    factory.protocol = SomeServerProtocol
    reactor.listenTCP(port, factory)
    reactor.run()
