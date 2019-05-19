#!/usr/bin/python3

# IMPORTANT
# WirinPi must be installed

import sys
import wiringpi
import ui
from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QDateTime, QCoreApplication
import time
import socket


# First 8 bit pins in Wiring Library 
byte = [17,18,27,22,23,24,25,4] # 8 bit data input MSB ---------- LSB
byteSelect = [5,6,13,19] # 4 bit for byte-selection GAL = 5, GAU = 6, GBL = 13, GBU = 19
reset = 20
relay = [12, 16]

wiringpi.wiringPiSetupGpio()
scan_interval=200 # ms


def setup_pi(): 
    wiringpi.wiringPiSetupGpio()
    
    for pins in byte:
        wiringpi.pinMode(pins, 0)
        wiringpi.pullUpDnControl(pins, 1) # PUD_OFF, (no pull up/down), PUD_DOWN (pull to ground) or PUD_UP 
        
    wiringpi.pinMode(reset, 1)
    wiringpi.digitalWrite(reset, 0);
    
    for opins in byteSelect:
        wiringpi.pinMode(opins, 1)
        wiringpi.digitalWrite(opins, 1)
       
    wiringpi.pinMode(relay[0], 1)
    wiringpi.pinMode(relay[1], 1)
    wiringpi.digitalWrite(relay[0], 1);
    wiringpi.digitalWrite(relay[1], 1);
    
    wiringpi.digitalWrite(reset, 1);
    wiringpi.delay(1000) # Delay for 1000 useconds


class portThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')
    
    def __init__(self, relay):
        QThread.__init__(self)
        self.relay = relay
         
    # run method gets called when we start the thread
    def run(self):
        print(self.relay)
        
        wiringpi.digitalWrite(self.relay, 0)
        wiringpi.delay(1000)
        wiringpi.digitalWrite(self.relay, 1) # HW has a contactor. So it only requires to have a ON signal for a short time. Otherwise this line can be commented off
        print(self.relay)
        
        self.signal.emit('timer out')

  
class timerThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')
    
    def __init__(self, on_time):
        QThread.__init__(self)
        self.ontime = on_time
         
    # run method gets called when we start the thread
    def run(self):
        print(self.ontime)
        wiringpi.delay(self.ontime)
        print(self.ontime)
        # time.sleep(((self.ontime)))
        self.signal.emit('timer out')
        print(self.ontime)
        print('t')
        

class CloneThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')
    wiringpi.wiringPiSetupGpio()
    def __init__(self, interval):
        QThread.__init__(self)
        self.interval = interval
         
    # run method gets called when we start the thread
    def run(self):
        
        while True:
            data = 0
            
            # reset the counter
            wiringpi.digitalWrite(reset, 0)
            wiringpi.delayMicroseconds(1)
            # wiringpi.delayMicroseconds(1)
            wiringpi.digitalWrite(reset, 1)
            # print(self.interval)
            
            #wiringpi.delay(self.interval-2) # Delay for interval ms
            time.sleep(((self.interval)/1000))
    
            wiringpi.digitalWrite(byteSelect[0], 0) # select the first byte
            data = wiringpi.digitalReadByte() # read the first 8 bits
            wiringpi.digitalWrite(byteSelect[0], 1)
            
            wiringpi.digitalWrite(byteSelect[1], 0) # select the first byte
            data |= (wiringpi.digitalReadByte() << 8)# read data
            wiringpi.digitalWrite(byteSelect[1], 1)
            
            wiringpi.digitalWrite(byteSelect[2], 0) # select the first byte
            data |= (wiringpi.digitalReadByte() << 16) # read data
            wiringpi.digitalWrite(byteSelect[2], 1)
            
            wiringpi.digitalWrite(byteSelect[3], 0) # select the first byte
            data |= (wiringpi.digitalReadByte() << 24) # read data
            wiringpi.digitalWrite(byteSelect[3], 1)
            
            countms = str(data*(1000/self.interval))
            #count = str(bin(data))
            self.signal.emit([data, countms, QDateTime.currentMSecsSinceEpoch()])
            #gui.liste_sayim.append(str(data*(1000/self.scan_interval)))
        
    
class Delta(QObject):
    
    signalStatus = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        
        # Create a gui object.
        self.gui = ui.Ui_Form()
        self.form = QtWidgets.QWidget()
        self.gui.setupUi(self.form)
        self.form.setGeometry(0, 40, 800, 450)
        self.gui.button_HW_off.setEnabled(False)
        
        self.gui.button_HW_off.clicked.connect(self.HWOFF)
        self.gui.button_HW_on.clicked.connect(self.HWON)
        self.gui.button_stop.clicked.connect(self.startStop)
        self.gui.button_clear.clicked.connect(self.clear)
        self.gui.button_save.clicked.connect(self.saveTXT)
        self.gui.button_close.clicked.connect(self.close)
        
        self.gui.on_time.setStyleSheet(
                               #"QSpinBox::up-arrow { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-bottom: 17px solid black; width: 0px; height: 0px; }"
                               #"QSpinBox::up-arrow:hover { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-bottom: 17px solid black; width: 0px; height: 0px; }"
                               "QSpinBox::up-button { width: 40px; height: 20px; }"
                               #"QSpinBox::up-button:hover { width: 40px; height: 20px; }"
 
                               #"QSpinBox::down-arrow { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-top: 17px solid black; width: 0px; height: 0px; }"
                               #"QSpinBox::down-arrow:hover { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-top: 17px solid black; width: 0px; height: 0px; }"
                               "QSpinBox::down-button { width: 40px; height: 20px; }"
                               #"QSpinBox::down-button:hover { width: 40px; height: 20px; }"
            )
        
        self.gui.interval.setStyleSheet(
                               #"QSpinBox::up-arrow { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-bottom: 17px solid black; width: 0px; height: 0px; }"
                               #"QSpinBox::up-arrow:hover { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-bottom: 17px solid black; width: 0px; height: 0px; }"
                               "QSpinBox::up-button { width: 40px; height: 20px; }"
                               #"QSpinBox::up-button:hover { width: 40px; height: 20px; }"
 
                               #"QSpinBox::down-arrow { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-top: 17px solid black; width: 0px; height: 0px; }"
                               #"QSpinBox::down-arrow:hover { border-left: 17px solid none;"
                               #"border-right: 17px solid none; border-top: 17px solid black; width: 0px; height: 0px; }"
                               "QSpinBox::down-button { width: 40px; height: 20px; }"
                               #"QSpinBox::down-button:hover { width: 40px; height: 20px; }"
            )
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.connect(("8.8.8.8", 80))
        self.gui.liste_sayim.append("IP Address : " + self.s.getsockname()[0])
        self.gui.liste_sayim.append(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()))
        self.s.close()
        self.timestamp = 0
#        self.gui_thread = CloneThread()  # This is the thread object
#        #Connect the signal from the thread to the finished method
#        self.gui_thread.signal.connect(self.finished)
#        self.gui_thread.start()
        
        self.state = 0 # data acquisition state


    def close(self):
        self.HWOFF()
        QCoreApplication.instance().quit()
       
        
    def clear(self):
        self.gui.liste_sayim.clear()
    
    
    def startStop(self):
        if self.state == 1: #stop
            self.gui.liste_sayim.append("Stop Acquisition")
            self.gui_thread.terminate()
            del self.gui_thread
            self.gui.button_stop.setText("Start Data Acquisition")
            self.state = 0
            self.gui.interval.setEnabled(True)
            self.timestamp = 0
        elif self.state == 0: #start
            self.gui.interval.setEnabled(False)
            scan_interval = self.gui.interval.value()
            self.gui_thread = CloneThread(scan_interval)  # This is the thread object
            self.gui_thread.signal.connect(self.finished)
            self.gui.liste_sayim.append("Interval : " + format(scan_interval))
            self.gui_thread.start()
            self.start_time = QDateTime.currentMSecsSinceEpoch() # start time in [ms]
            self.gui.liste_sayim.append("Start Acquisition")
            self.gui.liste_sayim.append(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()))
            self.gui.liste_sayim.append("Timestamp\tcount\tcount per sec")
            self.gui.button_stop.setText("Stop Data Acquisition")
            self.state = 1


    def saveTXT(self):
        fileName = "log" + time.strftime("%Y%m%d-%H%M%S") + ".txt"
        self.gui.liste_sayim.append("Saved to " + fileName)
        with open(fileName, 'w') as file:
            file.write(str(self.gui.liste_sayim.toPlainText()))


    def HWON(self):
        self.gui.liste_sayim.append("HW ON")
        self.gui.button_HW_off.setEnabled(True)
        self.gui.button_HW_on.setEnabled(False)
        
        if 'portOFF_thread' in locals():
            self.portOFF_thread.terminate()
            del self.portOFF_thread
        
        self.portON_thread = portThread(relay[0])  # This is the thread object
        self.portON_thread.start()
        
        # wiringpi.digitalWrite(relay[0], 0)
        # wiringpi.delay(1000)
        # wiringpi.digitalWrite(relay[0], 1)
        
        self.gui.button_HW_off.setFlat(True)
        self.palette = self.gui.button_HW_off.palette()
        self.role = self.gui.button_HW_off.backgroundRole() #choose whatever you like
        self.palette.setColor(self.role, QColor('red'))
        self.gui.button_HW_off.setPalette(self.palette)
        self.gui.button_HW_off.setAutoFillBackground(True)
        
        self.ontime_thread = timerThread(self.gui.on_time.value()*1000)  # This is the thread object
        self.ontime_thread.signal.connect(self.HWOFF)
        
        if self.gui.on_time.value() != 0:
            self.ontime_thread.start()


    def HWOFF(self):
        #print("BUTON")   
        self.gui.liste_sayim.append("HW OFF")
        self.gui.button_HW_off.setEnabled(False)
        self.gui.button_HW_on.setEnabled(True)
        
        if 'portOFF_thread' in locals():
            self.portOFF_thread.terminate()
            del self.portOFF_thread
        
        self.portOFF_thread = portThread(relay[1])  # This is the thread object
        self.portOFF_thread.start()

        # wiringpi.digitalWrite(relay[1], 0)
        # wiringpi.delay(1000)
        # wiringpi.digitalWrite(relay[1], 1)
        
        self.gui.button_HW_off.setFlat(False)
        self.gui.button_HW_off.setAutoFillBackground(True)
        
        if 'ontime_thread' in locals():
            self.ontime_thread.terminate()
            del self.ontime_thread


    def finished(self, result):
        #print("c")
        self.timestamp = result[2] - self.start_time
        self.gui.liste_sayim.append(format(self.timestamp) + "[ms]\t" + format(result[0]) + "\t" + format(result[1]))
        QtWidgets.QApplication.processEvents() #update gui for pyqt


def main():
    setup_pi()
    app = QtWidgets.QApplication(sys.argv)
    delta = Delta(app)
    delta.form.showFullScreen()
    #delta.form.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
