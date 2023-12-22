import socketio
import  socketio,os
from PyQt5.QtCore import pyqtSignal, QObject
ssl_cert_path='certifi/cacert.pem'
os.environ['SSL_CERT_FILE']=ssl_cert_path

class StreamElementsClient(QObject):
    giftedSubs = pyqtSignal(int)
    bits = pyqtSignal(int)
    resub = pyqtSignal()
    finished = pyqtSignal()
    def __init__(self, jwt):
        super().__init__()
        self.jwt = jwt
        self.connected=False
        # Initialize the Socket.IO client
        self.sio = socketio.Client()
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
        # print(data)
        print("on_event",data)
        if(data["type"]=='subscriber'):
            if( not data["data"].get("gifted",False) ):
                self.resub.emit() # resub
                return
            
            if(data.get("isMock",False)):
                if(data.get("activityGroup",None)==None):
                    self.giftedSubs.emit(1) # replayed direct gifted
                    return            

            # keys= list(self.gifted.keys())
            # activityGroup= data["activityGroup"]
            # if (not activityGroup in keys):
            #     self.gifted[activityGroup] = {"time":time.time(), "count":0}
            # self.gifted[activityGroup]["count"] += 1
            # if(self.gifted[activityGroup]["count"] == self.giftedReq ):
            #     if(self.giftedMulti):
            #         self.gifted[activityGroup]["count"] = 0
            #     self.giftedSubs.emit(self.giftedReq)
            
            # for key in list(self.gifted.keys()):
            #     if( time.time() - self.gifted[key]["time"] > 20 ):
            #         self.gifted.pop(key)

        elif(data["type"]=='communityGiftPurchase'):
            if(data.get("isMock",False)):
                amount = int(data["data"]["amount"])
                self.giftedSubs.emit(amount) # replayed bulk purchase gifted

        elif(data["type"]=='cheer'):
            amount = int(data["data"]["amount"])
            self.bits.emit(amount)
        # print(data)
        