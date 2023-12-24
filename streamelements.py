import socketio
import  socketio,os
from PyQt5.QtCore import pyqtSignal, QObject
ssl_cert_path='certifi/cacert.pem'
os.environ['SSL_CERT_FILE']=ssl_cert_path

class StreamElementsClient(QObject):
    giftedSubs = pyqtSignal(int,int)
    bits = pyqtSignal(int)
    finished = pyqtSignal()
    cachedSubs = {}
    def __init__(self, jwt):
        super().__init__()
        self.jwt = jwt
        self.connected=False
        # Initialize the Socket.IO client
        self.sio = socketio.Client(ssl_verify=False)
        # self.gifted={}
        # self.giftedReq=1
        # self.giftedMulti=True
        # Connect events to class methods
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('authenticated', self.on_authenticated)
        self.sio.on('unauthorized', self.on_unauthorized)
        self.sio.on('event', self.on_event)

    def close(self):
        self.disconnect()

    def change(self,jwt):
        if(jwt==self.jwt):
            return
        self.disconnect()
        self.jwt = jwt
        if(jwt==""):
            return
        self.connect()    

    def connect(self):
        # Connect to the server
        print("connect")
        self.sio.connect('https://realtime.streamelements.com', transports=['websocket'])

    def disconnect(self):
        # Disconnect from the server
        self.sio.disconnect()

    def authenticate_jwt(self):
        # Authenticate with JWT method
        self.sio.emit('authenticate', {'method': 'jwt', 'token': self.jwt})

    def on_connect(self):
        print('Successfully connected to the streamelements websocket')
        self.authenticate_jwt()  # You can switch to authenticate_jwt() if needed

    def on_disconnect(self):
        print('Disconnected from the streamelements websocket')
        # Reconnect or handle reconnection here

    def on_authenticated(self, data):
        channel_id = data['channelId']
        self.connected=True
        print(f'Successfully connected to channel {channel_id}')

    def on_unauthorized(self, data):
        self.connected=False
        print("on_unauthorized",data)

    def on_event(self, data,ts):
        if(data["type"]=='subscriber'):
            if(data.get("isMock",False) and (data["data"].get("gifted",False)) ):
                if(data.get("activityGroup",None)!=None):
                    activityGroup = data["activityGroup"]
                    if( activityGroup in list(self.cachedSubs.keys()) ):
                        amount= self.cachedSubs[activityGroup]
                        tier = int(data["data"].get("tier",1000))
                        tier = int(tier/1000)
                        self.cachedSubs.pop(activityGroup)
                        self.giftedSubs.emit(tier,amount)
                else:
                    tier = int(data["data"].get("tier",1000))
                    tier = int(tier/1000)
                    self.giftedSubs.emit(tier,1) # replayed direct gifted
                    return            

        elif(data["type"]=='communityGiftPurchase'):
            if(data.get("isMock",False)):
                amount = int(data["data"]["amount"])
                self.cachedSubs[data["activityGroup"]] = amount

        elif(data["type"]=='cheer'):
            amount = int(data["data"]["amount"])
            self.bits.emit(amount)
        # print(data)
        