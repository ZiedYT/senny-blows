from websocket import create_connection
from PyQt5.QtCore import pyqtSignal, QObject, QTimer
import json
import requests
import time 
import threading
import websocket
sslopt_ca_certs = {'ca_certs': 'certifi/cacert.pem'}

class Socket(QObject):
    giftedSubs = pyqtSignal(int,int)
    bits = pyqtSignal(int)
    resub = pyqtSignal()
    finished = pyqtSignal()
    def __init__(self,token,channel_name):
        super().__init__()
        self.mutex=False        
        self.run_flag=True
        self.valid=False
        self.client_id = 'gezmeh32vfe7xyd1hjuk1fgdlcsf1b'
        self.channel_name=""
        self.channelID=""
        self.token=""
        self.ws=self.createSocket()
        self.updateCredentials(channel_name,token)

        
    def run(self):        
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()
        pass


    def lock(self):
        while self.mutex:
            time.sleep(0.01)
        self.mutex=True
    
    def unlock(self):
        self.mutex=False

    def createSocket(self,url="wss://eventsub.wss.twitch.tv/ws"):
        ws = websocket.WebSocket(sslopt=sslopt_ca_certs)
        # ws = create_connection(url)
        ws.connect(url)
        welcome_msg = json.loads(ws.recv())
        print(welcome_msg)
        self.lock()
        self.session_id = welcome_msg["payload"]["session"]["id"]
        self.unlock()
        return ws

    def updateCredentials(self,channel_name,token):
        # if(  token=="" or channel_name==""):
        #     return
        if( token == self.token and channel_name == self.channel_name):
            return
        
        self.lock()
        self.channel_name = channel_name
        self.token = token
        self.headers={ 'Client-ID': self.client_id,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'} 
        self.unlock()

        # if( self.tokenValid()):
        self.channelID=self.getUserID(self.channel_name)
        if(self.channelID!=""):
            self.subscribe("channel.ban","1")
            self.subscribe("channel.subscription.gift","1")
            # self.subscribe("channel.subscribe","1")
            # self.subscribe("channel.subscription.message","1")
            # self.subscribe("channel.cheer","1")

    def getUserID(self,name):
        try:
            url = f'https://api.twitch.tv/helix/users?login={name}'
            response = requests.get(url, headers=self.headers).json()
            channelID= str(response["data"][0]["id"])
            return channelID
        except:
            return ""
    
    def subscribe(self,TYPE, VERSION):
        body={
                'type': TYPE,
                'version':VERSION,
                'condition': {
                    'broadcaster_user_id': self.channelID
                },
                'transport': {
                    'method': 'websocket',
                    'session_id': self.session_id
                }
            }
        
        res = requests.post('https://api.twitch.tv/helix/eventsub/subscriptions', headers=self.headers, json=body).json()
        self.valid = (res.get("message","")!="subscription missing proper authorization")
        

    def reconnect(self):
        self.ws=self.createSocket()
        self.updateCredentials(self.channel_name,self.token)
        

    def tokenValid(self):
        if(self.channel_name =="" or self.token =="" or self.channelID=="" ):
            self.valid= False
            return False
        return self.valid
    
        
    def spin(self):
        while self.run_flag:
            if(not self.tokenValid()):
                time.sleep(0.1)
                continue

            try:
                msg=json.loads(self.ws.recv())
            except Exception as e:
                if(self.run_flag ):
                    print(e,"Error listening to twich token, reconnecting")
                    if(not "Expecting value" in e):
                        self.reconnect()
                continue

            if(self.channel_name == "ziedyt" and msg["metadata"]["message_type"]!="session_keepalive"):
                
                self.giftedSubs.emit(1,1)

            if( msg["metadata"]["message_type"]!="session_keepalive"):
                msgType= msg["payload"]['subscription']["type"]
                print(msg)
                print("-------------------")
                if ( msgType== "channel.subscription.gift"):
                    amount = int(msg["payload"]["event"]["total"])
                    tier = int(msg["payload"]["event"].get("tier",1000))
                    if(type(tier)!=int):
                        tier=1000
                    tier = int(tier/1000)
                    self.giftedSubs.emit(tier,amount)

    def close(self):
        self.run_flag=False
        if(not self.valid):
            return
        import requests
        headers = {
            'Authorization': 'Bearer {}'.format(self.token),
            'Client-Id': '{}'.format(self.client_id),
        }
        response = requests.get('https://api.twitch.tv/helix/eventsub/subscriptions', headers=headers)
        for sub in response.json()["data"]:
            headers = {
            'Authorization': 'Bearer {}'.format(self.token),
            'Client-Id': '{}'.format(self.client_id),
            }

            params = {
                'id': '{}'.format(sub["id"]),
            }
            response = requests.delete('https://api.twitch.tv/helix/eventsub/subscriptions', params=params, headers=headers)
        
        self.ws=None
