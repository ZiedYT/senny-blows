import serial 
import time 
import threading 
import serial.tools.list_ports

class arduino:
    def __init__(self,port=''):
        self.mutex=False
        self.com= None
        self.port=port            

        self.queue=[]
        self.run_flag = True
        self.duration=1
        self.thread=threading.Thread(target=self.spin)
        self.thread.start()

    def lock(self):
        while self.mutex:
            time.sleep(0.01)
        self.mutex=False

    def unlock(self):
        self.mutex=False

    def addQueue(self,count=1):
        self.lock()
        for i in range(count):
            self.queue.append("")
        self.unlock

    def changePort(self,port):
        if(port==""):
            return False       
        try:
            if( self.com==None):
                self.port=port
                self.com= serial.Serial(port=port, baudrate=115200, timeout=.1)  

            elif(port!=self.port):
                self.com.close()
                self.port=port
                self.com= serial.Serial(port=port, baudrate=115200, timeout=.1)
            return True
        except:
            return False
        
    def write(self,x): 
        print("Sending {} to USB.".format(x))
        if(self.com==None):
            return
        msg=x+"\n"
        self.com.write( bytes(msg, 'utf-8')) 
        
    def spin(self):
        while self.run_flag:
            if( len(self.queue) == 0): # no queue
                time.sleep(0.1)
                continue
            
            self.lock()
            self.queue.pop()
            self.unlock

            self.write("1")
            time.sleep(self.duration)

            if( len(self.queue) == 0):
                self.write("0")

    def close(self):
        self.run_flag=False
        if(self.com!=None):
            self.com.close()

# ports = list(serial.tools.list_ports.comports())
# for p in ports:
#     print(p.device)
#     print(p.description)