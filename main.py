
import sys, time, webbrowser
import serial.tools.list_ports
import os
import json
from PyQt5.QtWidgets import QApplication,QTabWidget,QDoubleSpinBox, QDialog, QMainWindow, QSystemTrayIcon, QMenu, QAction, QCheckBox, QComboBox, QSpinBox, QLineEdit, QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5 import QtCore, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, QEvent, QTimer
from twitchSocket import Socket
from streamelements import StreamElementsClient
from arduino import arduino

import ctypes
print("Starting....")
exename = sys.argv[0]

def hideConsole():
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)

def showConsole():
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 1)

if(not "_console.exe" in exename):
    hideConsole()

class MainWindow(QMainWindow):
    def __init__(self , app ):
        super().__init__()
        self.data={}
        self.ports=[]
        self.arduino=None
        self.socketStreamelements=None
        self.save_folder = os.path.join(os.getenv('APPDATA'), 'sennyblows')
        if(not os.path.isdir(self.save_folder)):
            os.mkdir(self.save_folder)

        self.initialize()
        self.connect()
        self.loadJson()

        self.start_listener()
        self.timer = QTimer()
        self.timer.timeout.connect(self.spin)
        self.timer.start(1000)
        self.Login()

    def initialize(self):
        uic.loadUi('main.ui', self)
        self.setWindowTitle("Senny likes blowing, by ZiedYT")        
        import ctypes
        myappid = 'sennyblows'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.show()
        self.connect_menu()
        self.setWindowIcon(QIcon('icon.png'))
        self.setMaximumWidth(self.width())
        self.setMaximumHeight(self.height())
        self.setMinimumWidth(self.width())
        self.setMinimumHeight(self.height())
        
    def connect_menu(self):
        self.menu = QMenu()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.png'))
        self.tray_icon.setToolTip("Senny Blows")
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
        # self.show_action = QAction('Show', self)
        # self.show_action.triggered.connect(self.maximise)
        # self.menu.addAction(self.show_action)
        self.quit_action = QAction('Quit', self)
        self.quit_action.triggered.connect(self.quit)
        self.menu.addAction(self.quit_action)

    def maximise(self):
        self.setWindowFlags(QtCore.Qt.Window)
        self.show()
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.move(self.loc.x(), self.loc.y())

    # def changeEvent(self, event):
    #     if event.type() == QEvent.WindowStateChange:
    #         if self.windowState() & QtCore.Qt.WindowMinimized:            
    #             self.loc = self.geometry()
    #             self.setWindowFlags(QtCore.Qt.Tool)
    #             return 
            
    def loadJson(self):
        jsonpath = os.path.join(self.save_folder,"data.json")
        self.data["bits"]={}
        self.data["giftedT1"]={}
        self.data["giftedT2"]={}
        self.data["giftedT3"]={}

        if(not os.path.isfile(jsonpath)):
            return
        
        tempdata={}
        with open(jsonpath) as json_file:
            tempdata=json.load(json_file)    


        self.data["channel_name"] = tempdata.get("channel_name","")
        self.data["streamelementstoken"] = tempdata.get("streamelementstoken","")
        self.data["twitchtoken"] = tempdata.get("twitchtoken","")
        self.lineEdit_twitchtoken.setText(self.data["twitchtoken"])

        self.lineEdit_channelname.setText(self.data["channel_name"] )
        self.lineEdit_SEtoken.setText(self.data["streamelementstoken"])
        self.doubleSpinBox_duration.setValue(tempdata.get("duration",1))
        self.checkBox_multiple.setChecked(tempdata.get("multiple",True))
        self.currport = tempdata.get("port","")

        self.checkBox_bits.setChecked( tempdata.get("bits",{}).get("use",False) )
        self.spinBox_bits_amount.setValue(tempdata.get("bits",{}).get("amount",100) )
        
        self.checkBox_giftedT1.setChecked( tempdata.get("giftedT1",{}).get("use",False) )
        self.spinBox_giftedT1_amount.setValue(tempdata.get("giftedT1",{}).get("amount",1) )
        self.checkBox_giftedT2.setChecked( tempdata.get("giftedT2",{}).get("use",False) )
        self.spinBox_giftedT2_amount.setValue(tempdata.get("giftedT2",{}).get("amount",1) )
        self.checkBox_giftedT3.setChecked( tempdata.get("giftedT3",{}).get("use",False) )
        self.spinBox_giftedT3_amount.setValue(tempdata.get("giftedT3",{}).get("amount",1) )

    def saveJson(self):
        self.data["port"] = self.comboBox_port.currentText()  
        self.data["duration"] = self.doubleSpinBox_duration.value()
        self.data["multiple"]= self.checkBox_multiple.isChecked()

        self.data["bits"]["use"] = self.checkBox_bits.isChecked()
        self.data["bits"]["amount"] = self.spinBox_bits_amount.value()
        self.data["giftedT1"]["use"] = self.checkBox_giftedT1.isChecked()
        self.data["giftedT1"]["amount"] = self.spinBox_giftedT1_amount.value()
        self.data["giftedT2"]["use"] = self.checkBox_giftedT2.isChecked()
        self.data["giftedT2"]["amount"] = self.spinBox_giftedT2_amount.value()
        self.data["giftedT3"]["use"] = self.checkBox_giftedT3.isChecked()
        self.data["giftedT3"]["amount"] = self.spinBox_giftedT3_amount.value()

        file = os.path.join(self.save_folder, 'data.json')
        with open(file, 'w') as outfile:
            json.dump(self.data, outfile)

    def connect(self):
        self.pushButton_token: QPushButton = self.findChild(QPushButton, "pushButton_token")
        self.tokenLink= "https://streamelements.com/dashboard/account/channels"
        self.pushButton_token.clicked.connect( lambda: webbrowser.open(self.tokenLink) )
        self.lineEdit_channelname: QLineEdit = self.findChild(QLineEdit, "lineEdit_channelname")
        self.lineEdit_SEtoken: QLineEdit = self.findChild(QLineEdit,"lineEdit_SEtoken")

        self.lineEdit_twitchtoken: QLineEdit = self.findChild(QLineEdit,"lineEdit_twitchtoken")
        self.pushButton_twitchtoken: QPushButton = self.findChild(QPushButton, "pushButton_twitchtoken")
        self.twitchtokenLink= "https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=gezmeh32vfe7xyd1hjuk1fgdlcsf1b&redirect_uri=https://twitchapps.com/tokengen/&scope=channel%3Aread%3Asubscriptions%20bits%3Aread%20channel%3Amoderate"
        self.pushButton_twitchtoken.clicked.connect( lambda: webbrowser.open(self.twitchtokenLink) )

        self.pushButton_login:QPushButton = self.findChild(QPushButton,"pushButton_login")
        self.pushButton_login.clicked.connect(self.Login)
        self.pushButton_manual:QPushButton=self.findChild(QPushButton,"pushButton_manual")
        self.pushButton_manual.clicked.connect(self.manualBullet)
        self.pushButton_connect:QPushButton=self.findChild(QPushButton,"pushButton_connect")
        self.pushButton_connect.clicked.connect(self.connectESP)
        self.comboBox_port:QComboBox = self.findChild(QComboBox,"comboBox_port")
        self.doubleSpinBox_duration:QDoubleSpinBox = self.findChild(QDoubleSpinBox,"doubleSpinBox_duration")
        self.doubleSpinBox_duration.valueChanged.connect(self.updateDuration)


        self.checkBox_giftedT1:QCheckBox = self.findChild(QCheckBox,"checkBox_giftedT1")
        self.spinBox_giftedT1_amount:QSpinBox=self.findChild(QSpinBox,"spinBox_giftedT1_amount")
        self.checkBox_giftedT2:QCheckBox=self.findChild(QCheckBox,"checkBox_giftedT2")
        self.spinBox_giftedT2_amount:QSpinBox=self.findChild(QSpinBox,"spinBox_giftedT2_amount")
        self.checkBox_giftedT3:QCheckBox=self.findChild(QCheckBox,"checkBox_giftedT3")
        self.spinBox_giftedT3_amount:QSpinBox=self.findChild(QSpinBox,"spinBox_giftedT3_amount")
        self.checkBox_bits:QCheckBox=self.findChild(QCheckBox,"checkBox_bits")
        self.spinBox_bits_amount:QSpinBox=self.findChild(QSpinBox,"spinBox_bits_amount")
        self.checkBox_multiple:QCheckBox=self.findChild(QCheckBox,"checkBox_multiple")

        self.spinBox_giftedT1_amount.valueChanged.connect(self.saveJson)
        self.spinBox_giftedT2_amount.valueChanged.connect(self.saveJson)
        self.spinBox_giftedT3_amount.valueChanged.connect(self.saveJson)
        self.spinBox_bits_amount.valueChanged.connect(self.saveJson)
        
    def connectESP(self):
        if(self.arduino!=None):
            indx= self.comboBox_port.currentIndex()
            res = self.arduino.changePort(self.port_names[indx] )            
            if(res):
                self.pushButton_connect.setText("Connected")
            else:
                self.pushButton_connect.setText("Connect")

    def updatePorts(self):
        ports = list(serial.tools.list_ports.comports())
        if(ports!=self.ports):
            self.currport = self.comboBox_port.currentText()
            self.ports = ports.copy()
            self.comboBox_port.clear()
            self.port_desc = []
            self.port_names= []
            for p in ports:
                self.port_desc.append(p.description)
                self.port_names.append(p.device)

            if(len(self.ports)>0):
                self.comboBox_port.addItems(self.port_desc)
                indx=0
                if(self.currport in self.port_desc):
                    indx = self.port_desc.index(self.currport)
                self.comboBox_port.setCurrentIndex(indx)
                self.currport= self.comboBox_port.currentText()
            else:
                self.currport=""
            
    

    def updateDuration(self):
        if(self.arduino==None):
            return
        self.arduino.duration= self.doubleSpinBox_duration.value()

    def Login(self):
        print("login")
        channel_name= self.lineEdit_channelname.text()
        twitchtoken=self.lineEdit_twitchtoken.text()        
        token=self.lineEdit_SEtoken.text()

        self.socketStreamelements.change(token)
        self.data["streamelementstoken"] = token
        self.socketTwitch.updateCredentials(channel_name,twitchtoken)
        # self.socketTwitch.tokenValid()
        self.data["twitchtoken"] = twitchtoken
        self.data["channel_name"]=channel_name

    def onGifted(self,tier,amount):
        print("sub; tier:",tier,";amount:",amount)
        spinbox:QSpinBox = self.findChild(QSpinBox,"spinBox_giftedT{}_amount".format(tier))
        checkbox:QCheckBox =self.findChild(QCheckBox,"checkBox_giftedT{}".format(tier))
        if(checkbox.isChecked()):
            mingifts= spinbox.value()
            if(amount>=mingifts):
                count = 1 
                if(self.checkBox_multiple.isChecked()):
                    count = int (amount / mingifts)
                self.arduino.addQueue(count)


    def onBits(self,amount):
        print("onBits",amount)
        if(not self.checkBox_bits.isChecked()):
            return
        if(self.checkBox_bits.isChecked()):
            minbits= self.spinBox_bits_amount.value()
            if(amount>=minbits):
                count = 1 
                if(self.checkBox_multiple.isChecked()):
                    count = int (amount / minbits)
                self.arduino.addQueue(count)

    def manualBullet(self):
        self.arduino.addQueue()


    def start_listener(self):
        # self.socketStreamelements = Socket()
        self.socketStreamelements = StreamElementsClient(self,self.lineEdit_SEtoken.text())
        self.socketStreamelements.connect() 
        self.qthreadStreamelements = QThread()
        self.socketStreamelements.moveToThread(self.qthreadStreamelements)

        # self.qthreadStreamelements.started.connect(self.socketStreamelements.run)
        self.socketStreamelements.finished.connect(self.qthreadStreamelements.quit)
        self.socketStreamelements.finished.connect(self.socketStreamelements.deleteLater)
        self.qthreadStreamelements.finished.connect(self.qthreadStreamelements.deleteLater)
        self.socketStreamelements.finished.connect(self.quit)

        self.socketStreamelements.giftedSubs.connect(self.onGifted)
        self.socketStreamelements.bits.connect(self.onBits)

        self.qthreadStreamelements.start()
        
        self.socketTwitch = Socket(self.lineEdit_twitchtoken.text(), self.lineEdit_channelname.text())
        self.qthreadTwitch = QThread()
        self.socketTwitch.moveToThread(self.qthreadTwitch)
        self.qthreadTwitch.started.connect(self.socketTwitch.run)
        self.socketTwitch.finished.connect(self.qthreadTwitch.quit)
        self.socketTwitch.finished.connect(self.socketTwitch.deleteLater)
        self.qthreadTwitch.finished.connect(self.qthreadTwitch.deleteLater)
        self.socketTwitch.giftedSubs.connect(self.onGifted)
        self.socketTwitch.finished.connect(self.quit)
        self.qthreadTwitch.start()

        self.arduino = arduino(port=self.data.get("port",""))
        self.arduino.duration=self.doubleSpinBox_duration.value()

    def spin(self):
        self.updatePorts()

        if(not self.socketTwitch.valid):
            self.lineEdit_twitchtoken.setStyleSheet("border: 3px solid red;")
        else:
            self.lineEdit_twitchtoken.setStyleSheet("border: 1px solid black;")

        if(not self.socketStreamelements.connected):
            self.lineEdit_SEtoken.setStyleSheet("border: 3px solid red;")
        else:
            self.lineEdit_SEtoken.setStyleSheet("border: 1px solid black;")

    def closeEvent(self, event):
        self.quit()

    def quit(self):
        self.socketStreamelements.close()
        # self.socketTwitch.close()
        self.saveJson()
        self.arduino.run_flag=False
        self.socketStreamelements.run_flag=False
        self.tray_icon.hide()
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(app)    
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(str(e))
        window.quit()
