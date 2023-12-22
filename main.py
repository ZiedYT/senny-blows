
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
        self.data["gifted"]={}
        self.data["subs"]={}

        if(not os.path.isfile(jsonpath)):
            return
        
        tempdata={}
        with open(jsonpath) as json_file:
            tempdata=json.load(json_file)    

        # tempdata = json.load(jsonpath) 
        self.data["channel_name"] = tempdata.get("channel_name","")
        self.data["streamelementstoken"] = tempdata.get("streamelementstoken","")
        self.data["twitchtoken"] = tempdata.get("twitchtoken","")
        self.lineEdit_channelname.setText(self.data["channel_name"] )
        self.lineEdit_SEtoken.setText(self.data["streamelementstoken"])
        self.lineEdit_twitchtoken.setText(self.data["twitchtoken"])
        self.checkBox_active.setChecked(tempdata.get("active",False) )
        self.doubleSpinBox_duration.setValue(tempdata.get("duration",0.5))
        self.currport = tempdata.get("port","")
        # self.updatePorts()

        self.checkBox_bits.setChecked( tempdata.get("bits",{}).get("use",False) )
        self.spinBox_amountbits.setValue(tempdata.get("bits",{}).get("amount",100) )
        self.checkBox_mutiplebits.setChecked( tempdata.get("bits",{}).get("multi",False) )

        self.checkBox_gifted.setChecked( tempdata.get("gifted",{}).get("use",False) )
        self.spinBox_amountgifted.setValue(tempdata.get("gifted",{}).get("amount",100) )
        self.checkBox_mutiplegifted.setChecked( tempdata.get("gifted",{}).get("multi",False) )

        self.checkBox_subs.setChecked(tempdata.get("subs",{}).get("use",False))

    def saveJson(self):
        
        self.data["port"] = self.comboBox_port.currentText()
        self.data["active"] = self.checkBox_active.isChecked()        
        self.data["duration"] = self.doubleSpinBox_duration.value()

        self.data["bits"]["use"] = self.checkBox_bits.isChecked()
        self.data["bits"]["multi"] = self.checkBox_mutiplebits.isChecked()
        self.data["bits"]["amount"] = self.spinBox_amountbits.value()

        self.data["gifted"]["use"] = self.checkBox_gifted.isChecked()
        self.data["gifted"]["multi"] = self.checkBox_mutiplegifted.isChecked()
        self.data["gifted"]["amount"] = self.spinBox_amountgifted.value()

        self.data["subs"]["use"] = self.checkBox_subs.isChecked()

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
        self.checkBox_active: QCheckBox = self.findChild(QCheckBox, "checkBox_active")
        self.checkBox_gifted: QCheckBox = self.findChild(QCheckBox,"checkBox_gifted")
        self.checkBox_subs: QCheckBox = self.findChild(QCheckBox,"checkBox_subs")
        self.checkBox_bits: QCheckBox = self.findChild(QCheckBox,"checkBox_bits")
        self.checkBox_mutiplegifted: QCheckBox = self.findChild(QCheckBox,"checkBox_mutiplegifted")
        self.checkBox_mutiplebits: QCheckBox = self.findChild(QCheckBox,"checkBox_mutiplebits")
        self.spinBox_amountgifted:QSpinBox = self.findChild(QSpinBox,"spinBox_amountgifted")
        self.spinBox_amountbits:QSpinBox = self.findChild(QSpinBox,"spinBox_amountbits")
        self.comboBox_port:QComboBox = self.findChild(QComboBox,"comboBox_port")
        self.doubleSpinBox_duration:QDoubleSpinBox = self.findChild(QDoubleSpinBox,"doubleSpinBox_duration")
        self.doubleSpinBox_duration.valueChanged.connect(self.updateDuration)
        self.pushButton_manual:QPushButton=self.findChild(QPushButton,"pushButton_manual")
        self.pushButton_manual.clicked.connect(self.manualBullet)
        self.pushButton_connect:QPushButton=self.findChild(QPushButton,"pushButton_connect")
        self.pushButton_connect.clicked.connect(self.connectESP)


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
        channel_name= self.lineEdit_channelname.text()
        twitchtoken=self.lineEdit_twitchtoken.text()        
        token=self.lineEdit_SEtoken.text()

        self.socketStreamelements.change(token)
        self.data["streamelementstoken"] = token

        self.socketTwitch.updateCredentials(twitchtoken,channel_name)
        self.data["twitchtoken"] = twitchtoken
        self.data["channel_name"]=channel_name

        # self.data["token"] = token

        # # self.socketStreamelements.updateCredentials(self.data["channel_name"], self.data["token"])
        # if(not self.socketStreamelements.valid):
        #     self.lineEdit_token.setStyleSheet("border: 3px solid red;")
        # else: 
        #     self.lineEdit_token.setStyleSheet("border: 1px solid black;")

    def onSub(self):
        print("onSub")
        if(not self.checkBox_active.isChecked()):
            return
        if (self.checkBox_subs.isChecked()):
            self.arduino.addQueue()

    def onGifted(self,amount):
        print("onGifted",amount)
        if(not self.checkBox_active.isChecked()):
            return
        if(self.checkBox_gifted.isChecked()):
            mingifts= self.spinBox_amountgifted.value()
            if(amount>=mingifts):
                count = 1 
                if(self.checkBox_mutiplegifted.isChecked()):
                    count = int (amount / mingifts)
                self.arduino.addQueue(count)

    def onBits(self,amount):
        print("onBits",amount)
        if(not self.checkBox_active.isChecked()):
            return
        if(self.checkBox_bits.isChecked()):
            minbits= self.spinBox_amountbits.value()
            if(amount>=minbits):
                count = 1 
                if(self.checkBox_mutiplebits.isChecked()):
                    count = int (amount / minbits)
                self.arduino.addQueue(count)

    def manualBullet(self):
        self.arduino.addQueue()


    def start_listener(self):
        # self.socketStreamelements = Socket()
        self.socketStreamelements = StreamElementsClient(self.lineEdit_SEtoken.text())
        self.socketStreamelements.connect() 
        self.qthreadStreamelements = QThread()
        self.socketStreamelements.moveToThread(self.qthreadStreamelements)

        # self.qthreadStreamelements.started.connect(self.socketStreamelements.run)
        self.socketStreamelements.finished.connect(self.qthreadStreamelements.quit)
        self.socketStreamelements.finished.connect(self.socketStreamelements.deleteLater)
        self.qthreadStreamelements.finished.connect(self.qthreadStreamelements.deleteLater)
        self.socketStreamelements.finished.connect(self.quit)

        self.socketStreamelements.resub.connect(self.onSub)
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
        self.socketTwitch.close()
        self.saveJson()
        self.arduino.run_flag=False
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
