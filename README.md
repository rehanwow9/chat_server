# Messaging Server

Simple messaging server which brokers messages from one device to another tagged with its destination id.


Modified the code of http://pawelmhm.github.io/python/websockets/2016/01/02/playing-with-websockets.html to handle the requirements of messaging.

### Prequisites

You will need to have the below application and libraries to run this:

* [Python 3.5]
* [virtualenv]

### Installation



You need virtualenv installed globally:


In Ubuntu:
```sh
$ sudo apt-get install virtualenv
```

Clone the repository:

```sh
$ git clone https://github.com/rehanwow9/chat_server.git
$ cd chat_server
```

Activate the virtual environment:

```sh
$ virtualenv venv
$ virtualenv -p /usr/bin/python3.5 venv
$ source venv/bin/activate
```

Install the required libraries through pip:

```sh
(venv)$ pip3 install -r requirements.txt
```

Run the server's python file:

```sh
(venv)$ python server.py
```

And voila! The web-socket server is now running on port 8080 and is ready to connect clients!

You can change the port number in the server.cfg file if you like to.

### Client-Side

You can find a index.html in the folder if you like to test the code locally. However, any web-socket client can connect to this in the network provided you give the correct address when connecting, in the format 'ws://host:port'

There are two queries to be played around with:

 - help:  This returns your device id, list of ids of connected devices, and the usage of the send message query.

 - send,<destinationID>,<msg> : eg. send,100000001,hello

### Implementation

Upon successful connection of a client a dictionary item is added to the clients dict, where the key is the destination Id and value is the ClientModel. Also a mapping of the client-peer to the same destination Id is done for simplification of querying. This is done in the register function of the WebSocketServerFactory

```python
def register(self, client):
    """
    Add client to list of managed connections.
    """
    destinationId = self.currID
    self.currID += 1
    self.clients[destinationId] = ClientModel(client)
    self.peerToDestinationMap[client.peer] = destinationId
```

The ClientModel is as follows:

```python
class ClientModel(object):
    def __init__(self, client):
        """Store the client, and initialize lastMessage sent
        and the time at which it was sent"""
        self.client = client
        self.lastMessageTime = datetime.datetime.now()
        self.lastMessage = None

    def updateLastMessage(self, msg):
        """After a successful message sent update the lastMessage"""
        self.lastMessage = msg
        self.lastMessageTime = datetime.datetime.now()

    def isDuplicate(self, msg):
        """Check whether the last message sent is same as the current one to be sent
        and the difference in time is no more than 5 seconds"""
        return (self.lastMessage == msg) and ((datetime.datetime.now() - self.lastMessageTime).seconds < 5)
```

The communicate function of the factory is where the major logic resides. It parses the query string received from the client, extracts the destination id and the message to be sent to that destination id, and then finally sends the message to that device if available. It also checks for duplicate messages, i.e., same message sent by a client to same or other client within 5 seconds time interval.

```python
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
```

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)


   [Python 3.5]: <https://www.python.org/downloads/release/python-350/>
   [virtualenv]: <http://docs.python-guide.org/en/latest/dev/virtualenvs/>
