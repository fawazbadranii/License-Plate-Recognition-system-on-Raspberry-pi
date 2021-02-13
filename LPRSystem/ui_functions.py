################################################################################
##
## BY: WANDERSON M.PIMENTA
## PROJECT MADE WITH: Qt Designer and PySide2
## V: 1.0.0
##
################################################################################

## ==> GUI FILE
from main import *
from ui_main import *
import sys
import threading
#import sensor use sensor.roatateMotor()

t1 = None
#from sensor import *
import sensor as sen
#import sensor as sen
def openGate():
    sen.checkDistance= False
    sen.rotateMotor()
    sen.checkDistance= True
    #threading.current_thread().join()
    #t1 = threading.current_thread()
    #t1.kill()
    #t1.kill()

class UIFunctions(MainWindow):  #insert Window in paraentesis

    def clickedButton(self):
        threading.Timer(0.1, openGate).start()
        print("Opening gate")
        #self.ui.label_8.setText("Button clicked")

        
    def closeEvent(self):
#         os._exit
        sen.Shutdown = True
        print("GUI Closed")
        sen.checkDistance= False
        #Your desired functionality here
        with open('sensor.py', 'r'): #open the file
            KeyboardInterrupt #put the lines to a variable.
            print('Close button pressed')
            
        
        
    
