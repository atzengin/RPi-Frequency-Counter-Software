#!/usr/bin/python3

# IMPORTANT
# WiringPi must be installed

import sys
import wiringpi
import ui
from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QObject, QDateTime, QCoreApplication
import time
import socket
import os


# Read first 16 bits of Wiring Pins
byte1 = [17,18,27,22,23,24,25,4] # 8 bit data input LSB ---------- MSB
byte2 = [2,3,8,7,10,9,11,14] # 8 bit data input LSB ---------- MSB
byteSelect = [5,6,13,19] # 4 bit for byte-selection GAL = 5, GAU = 6, GBL = 13, GBU = 19
reset = 20
relay = [12, 16]
rclk = 26
   
# See this page for setup :http://wiringpi.com/reference/setup/ 
wiringpi.wiringPiSetupGpio()
#wiringpi.wiringPiSetupSys()


def setup_pi(): 
    print("setup_pi started")
    wiringpi.wiringPiSetupGpio()
    
    for pins in byte1:
        wiringpi.pinMode(pins, 0)
        wiringpi.pullUpDnControl(pins, wiringpi.PUD_DOWN) # PUD_OFF, (no pull up/down), PUD_DOWN (pull to ground) or PUD_UP 
        
    for pins in byte2:
        wiringpi.pinMode(pins, 0)
        wiringpi.pullUpDnControl(pins, wiringpi.PUD_DOWN) # PUD_OFF, (no pull up/down), PUD_DOWN (pull to ground) or PUD_UP 
        
    wiringpi.pinMode(reset, 1)
    wiringpi.digitalWrite(reset, 0);
    
    #wiringpi.pinMode(rclk, 1)
    #wiringpi.digitalWrite(rclk, 0);
    
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
    print("portThread created")
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
    print("timerThread created")
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
        

class dataAcquisitionTimer(QObject):
    signal = pyqtSignal('PyQt_PyObject')
    
    def __init__(self, interval):
        QThread.__init__(self)
        
        self.interval = interval
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.getData)
        self.data_timer.start(self.interval)
        
    def stop(self):
        self.data_timer.stop()
        del self.data_timer
        
    def getData(self):
        self.currentTime = QDateTime.currentMSecsSinceEpoch()
        
        wiringpi.digitalWrite(byteSelect[0], 0) # select the first byte
        self.data1 = self.read(0) # read first counter
        self.data5 = self.read(1) # read second counter
        wiringpi.digitalWrite(byteSelect[0], 1)
        
        wiringpi.digitalWrite(byteSelect[1], 0) # select the second byte
        self.data2 = self.read(0) # read first counter
        self.data6 = self.read(1) # read second counter
        wiringpi.digitalWrite(byteSelect[1], 1)
        
        wiringpi.digitalWrite(byteSelect[2], 0) # select the third byte
        self.data3 = self.read(0) # read first counter
        self.data7 = self.read(1) # read second counter
        wiringpi.digitalWrite(byteSelect[2], 1)
        
        wiringpi.digitalWrite(byteSelect[3], 0) # select the forth byte
        self.data4 = self.read(0) # read first counter
        self.data8 = self.read(1) # read second counter
        wiringpi.digitalWrite(byteSelect[3], 1)
        
        # reset the counter
        wiringpi.digitalWrite(reset, 0)
        wiringpi.delayMicroseconds(1)
        wiringpi.digitalWrite(reset, 1)
        
        self.data_cnt1 = (self.data4<<24) | (self.data3<<16) | (self.data2<<8) | (self.data1)
        self.data_cnt2 = (self.data8<<24) | (self.data7<<16) | (self.data6<<8) | (self.data5)
        self.countms_cnt1 = str(self.data_cnt1*(1000/self.interval))
        self.countms_cnt2 = str(self.data_cnt2*(1000/self.interval))

        self.signal.emit([self.data_cnt1, self.countms_cnt1, self.data_cnt2, self.countms_cnt2, self.currentTime])
        
    def read(self, byte):
        self.veri = 0
        for i in reversed(range(byte*8, (byte*8)+8)):
            self.x = wiringpi.digitalRead(wiringpi.wpiPinToGpio(i))
            self.veri = (self.veri << 1) | self.x

        return self.veri


class Delta(QObject):
    
    signalStatus = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        
        # Create a gui object.
        self.gui = ui.Ui_Form()
        self.form = QtWidgets.QWidget()
        self.gui.setupUi(self.form)
        self.form.setGeometry(0, 40, 800, 450)
        self.form.setWindowTitle('Pulse Counter')
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
        
        self.timestamp = 0
        self.updateInfo()
        self.state = 0 # data acquisition state


    def close(self):
        self.HWOFF()
        if self.gui.checkbox_send_TCP.isChecked() == 1:
            try:
                self.s.sendall(b'close')
            except:
                print('Close TCP signal has not been sent!')
        QCoreApplication.instance().quit()
       
        
    def clear(self):
        
        qm = QtWidgets.QMessageBox
        self.reply = qm.question(None,'Warning', "Are you sure to clear logs? Be sure if they are saved!", qm.Yes | qm.No)

        if self.reply == qm.Yes:
            self.gui.liste_sayim.clear()
            self.updateInfo()
    
    
    def updateInfo(self):
        
        self.gui.liste_sayim.append(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()))
        self.gui.labelCH1.setText("")
        self.gui.labelCH2.setText("")
        self.f = os.popen("ifconfig wlan0 | grep \"inet\ \" | awk '{print $2}'")
        self.ip = self.f.read()
        print("IP Address : " + str(self.ip))
        self.gui.liste_sayim.append('IP Address : '+ str(self.ip))
    
    
    def startStop(self):
        if self.state == 1: #stop
            print("data acquisition stopped")
            self.gui.liste_sayim.append("Timestamp\tCH1 Count\tCH1 Count/sec\tCH2 Count\tCH2 Count/sec")
            self.gui.liste_sayim.append("Stop Acquisition")
            
            self.gui_timer.stop()
            del self.gui_timer
            
            self.gui.button_stop.setText("Start Acquisition")
            self.state = 0
            self.gui.interval.setEnabled(True)
            self.gui.checkbox_send_TCP.setEnabled(True)
            self.gui.lineEdit_IP.setEnabled(True)
            self.gui.lineEdit_Port.setEnabled(True)
            self.timestamp = 0
        elif self.state == 0: #start
            print("data acquisition started")
            self.gui.interval.setEnabled(False)
            self.gui.checkbox_send_TCP.setEnabled(False)
            self.gui.lineEdit_IP.setEnabled(False)
            self.gui.lineEdit_Port.setEnabled(False)
            scan_interval = self.gui.interval.value()
            
            self.gui_timer = dataAcquisitionTimer(scan_interval)
            self.firstData = 10  # how many count data will be dropped at first
            self.gui_timer.signal.connect(self.finished)
            self.gui.liste_sayim.append("Interval : " + format(scan_interval) + " ms")
            
            self.gui.liste_sayim.append("Start Acquisition")
            self.gui.liste_sayim.append(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()))
            self.gui.liste_sayim.append("Timestamp\tCH1 Count\tCH1 Count/sec\tCH2 Count\tCH2 Count/sec")
            self.gui.button_stop.setText("Stop Acquisition")
            
            if self.gui.checkbox_send_TCP.isChecked() == 1:
                try:
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #self.s.connect((TCP_IP , TCP_PORT))
                    self.s.connect((self.gui.lineEdit_IP.text(), int(self.gui.lineEdit_Port.text())))
                    self.s.sendall(b'Connected')
                    print('TCP Connection OK')
                    self.gui.liste_sayim.append('TCP Connection OK')
                except:
                    print('TCP Connection NG!')
                    self.gui.liste_sayim.append('TCP Connection NG!')
            
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
        #print(self.state)
        
        if self.firstData > 0:
            # do nothing. drop first data. 
            # will find more innovative solution here!
            self.firstData -= 1
            self.start_time = result[4] # get starting time
            self.gui.liste_sayim.append('Starting in ' + str(self.firstData))
            
        else:

            self.timestamp = result[4] - self.start_time
            self.gui.liste_sayim.append(format(self.timestamp) + "[ms]\t" + format(result[0]) + "\t" + format(result[1]) + "\t" + format(result[2]) + "\t" + format(result[3]))
            self.gui.labelCH1.setText( str( float("{0:.2f}".format(float(result[1])/1000)) ) + "\tkHz")
            self.gui.labelCH2.setText( str( float("{0:.2f}".format(float(result[3])/1000)) ) + "\tkHz")
            #print(result[0])
            #print(type(bytes(str(result[0]), 'utf-8')))
            
            if self.gui.checkbox_send_TCP.isChecked() == 1:
                try:
                    self.s.sendall(bytes(str(result), 'utf-8'))
                except:
                    print('TCP send error!')
                    self.gui.liste_sayim.append('TCP send error!')
            
            #self.s.sendall(b'tarik')
            QtWidgets.QApplication.processEvents() #update gui for pyqt


def main():
    setup_pi()
    app = QtWidgets.QApplication(sys.argv)
    delta = Delta(app)
    #delta.form.showFullScreen()
    #delta.form.show()
    delta.form.showMaximized()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
