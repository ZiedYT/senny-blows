import socketio
import  socketio,os
from PyQt5.QtCore import pyqtSignal, QObject
import time
import threading
ssl_cert_path='certifi/cacert.pem'
os.environ['SSL_CERT_FILE']=ssl_cert_path

class StreamElementsClient(QObject):
    giftedSubs = pyqtSignal(int,int)
    bits = pyqtSignal(int)
    finished = pyqtSignal()
    cachedSubs = {}
    def __init__(self,front, jwt):
        super().__init__()
        self.useGifted=False
        self.run_flag=True
        self.mutex=False
        self.jwt = jwt
        self.front=front
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
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def lock(self):
        while self.mutex:
            time.sleep(0.01)
        self.mutex=True

    def unlock(self):
        self.mutex=False

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
    def spin(self):
        while self.run_flag:
            self.useGifted = self.front.data["twitchtoken"]==""

            keys  =list(self.cachedSubs.keys()) 
            if( len (keys) ==0):
                time.sleep(0.1)
                continue
            for activityGroup in keys:
                self.lock()
                activityGroup = keys[0]
                lastTime = self.cachedSubs[ activityGroup ]["time"]
                amount = self.cachedSubs[ activityGroup ]["amount"]
                tier = self.cachedSubs[ activityGroup ]["tier"]
                emitted = self.cachedSubs[ activityGroup ]["emitted"]
                req=0
                if(tier!="tier"):
                    req = self.front.data["giftedT{}".format(tier)]["amount"]
                bulkamount=self.cachedSubs[activityGroup].get("bulkamount",0)
                
                if(bulkamount!=0 and tier!="tier" ):
                    if(bulkamount>0):
                        self.giftedSubs.emit(tier,bulkamount)
                    self.cachedSubs[ activityGroup ]={ "amount":0,"time":lastTime,"tier":tier,"bulkamount":-1,"emitted":True}
                
                elif( amount>=req and bulkamount==0 ):
                    self.cachedSubs[ activityGroup ]={ "amount":amount-req,"time":lastTime,"tier":tier,"emitted":True}
                    if( self.useGifted and (self.front.checkBox_multiple.isChecked()  or not emitted) ):
                        self.giftedSubs.emit(tier,req)

                elif(time.time() - lastTime>1):
                    self.cachedSubs.pop(activityGroup)
                    self.unlock()
                    break
                self.unlock()

    def on_event(self, data,ts):
        # if(data["type"]=='subscriber'):
        #     if(data.get("isMock",False) and (data["data"].get("gifted",False)) ):
        #         if(data.get("activityGroup",None)!=None):
        #             activityGroup = data["activityGroup"]
        #             if( activityGroup in list(self.cachedSubs.keys()) ):
        #                 amount= self.cachedSubs[activityGroup]
        #                 tier = int(data["data"].get("tier",1000))
        #                 tier = int(tier/1000)
        #                 self.cachedSubs.pop(activityGroup)
        #                 self.giftedSubs.emit(tier,amount)
        #         else:
        #             tier = int(data["data"].get("tier",1000))
        #             tier = int(tier/1000)
        #             self.giftedSubs.emit(tier,1) # replayed direct gifted
        #             return     
               
    
                    
        # elif(data["type"]=='communityGiftPurchase'):
        #     if(data.get("isMock",False)):
        #         amount = int(data["data"]["amount"])
        #         self.cachedSubs[data["activityGroup"]] = amount
            

        if(data["type"]=='subscriber'):
            # print(data)
            if( data.get("activityGroup","")!=""  ): # gifted subs
                if(data["data"].get("gifted",False) ): 
                    activityGroup= data["activityGroup"]
                    tier = data["data"].get("tier",1000)
                    if(tier=="prime"):
                        tier=1000
                    tier = int( int(tier)/1000)  
                    self.lock()
                    
                    if(not activityGroup in list(self.cachedSubs.keys()) ):
                        self.cachedSubs[activityGroup] = { "amount":0,"time":time.time(),"tier":tier,"emitted":False}
                    bulkamount=self.cachedSubs[activityGroup].get("bulkamount",0)
                    emitted= self.cachedSubs[ activityGroup ]["emitted"]
                    if(bulkamount!=0): # part of bulk replay, get tier
                        self.cachedSubs[ activityGroup ] = { "amount":0,"time":time.time(),"tier":tier,"bulkamount":bulkamount,"emitted":emitted}
                        
                    else: # not part of replay, increase sub count
                        amount = self.cachedSubs[ activityGroup ]["amount"]+1
                        emitted= self.cachedSubs[ activityGroup ]["emitted"]
                        self.cachedSubs[ activityGroup ] = { "amount":amount,"time":time.time(),"tier":tier,"emitted":emitted}
                    self.unlock()

            elif(data["data"].get("gifted",False)  ): # direct gifted
                tier = data["data"].get("tier",1000)
                if(tier=="prime"):
                    tier=1000
                tier = int( int(tier)/1000)  
                if( self.useGifted):
                    self.giftedSubs.emit(tier,1) 
                return                  
              
            elif(  not data["data"].get("gifted",False)): # normal sub
                tier = data["data"].get("tier",1000)
                if(tier=="prime"):
                    tier=1000
                tier = int( int(tier)/1000)    
                self.giftedSubs.emit(tier,1)

        elif(data["type"]=="communityGiftPurchase" and not self.useGifted): # only on mock, bulk gifted
            self.lock()
            activityGroup=data["activityGroup"]
            amount=data["data"]["amount"]
            self.cachedSubs[activityGroup] = { "amount":0,"time":time.time(),"tier":"tier","bulkamount":amount,"emitted":False}
            self.unlock()

        elif(data["type"]=='cheer'):
            amount = int(data["data"]["amount"])
            self.bits.emit(amount)
        # print(data)
        