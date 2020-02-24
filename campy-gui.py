#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel
import PyQt5.QtCore as Core 
import cv2
import sys
import datetime
import os
import camcontrol as cc

class MainApp(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.setup_ui()
        
        self.update_totTime()
        self.timer = QTimer()
        self.camera = cc.camcontrol()
        
        self.savepath = os.getcwd()
        self.label_folder.setText(self.savepath)
        self.on_caminfos()
        #self.setup_camera()

    def setup_ui(self):
        """Initialize widgets.
        """
        
        ########## groupbox for folder selection
        
        self.btn_folder = QPushButton("change folder")
        self.btn_folder.clicked.connect(self.on_folder)        
        self.label_folder = QLabel('')

        self.group_folder = QGroupBox("Project folder")
        self.layout_group_cam = QHBoxLayout()
        self.layout_group_cam.addWidget(self.btn_folder)#,stretch=1)
        self.layout_group_cam.addWidget(self.label_folder,stretch=1)#,stretch=4)
        self.group_folder.setLayout(self.layout_group_cam)
        
        
        ######### groupbox for camsettings
        
        self.btn_caminfos = QPushButton("update available cameras")
        self.btn_caminfos.clicked.connect(self.on_caminfos)

        self.combo_cams = QComboBox()
        
        self.combo_res = QComboBox()
        self.combo_res.addItems(["640x480", "800x600", "1024x768", "1280x720", "1280x1024"])
        
        self.label_res = QLabel("current: ")
        
        self.btn_runcam = QPushButton("open selected cam")
        self.btn_runcam.clicked.connect(self.on_runcam)

        self.btn_closecam = QPushButton("close cam")
        self.btn_closecam.clicked.connect(self.on_closecam)
        
        self.check_autoExposure = QCheckBox("disable auto-brightness")
        self.check_autoExposure.stateChanged.connect(self.update_camsetting)
        
        self.group_cam = QGroupBox("Camera settings")
        self.layout_group_cam = QGridLayout()
        self.layout_group_cam.addWidget(QLabel("camera index:"),0,0)
        self.layout_group_cam.addWidget(self.combo_cams,0,1)
        self.layout_group_cam.addWidget(QLabel("resolution:"),1,0)
        self.layout_group_cam.addWidget(self.combo_res,1,1)
        self.layout_group_cam.addWidget(self.label_res,1,2)
        self.layout_group_cam.addWidget(self.btn_caminfos,0,2)
        self.layout_group_cam.addWidget(self.check_autoExposure,2,0,1,3)
        self.layout_group_cam.addWidget(self.btn_runcam,3,0)
        self.layout_group_cam.addWidget(self.btn_closecam,3,1)
        self.group_cam.setLayout(self.layout_group_cam)
        
        ######### used for display images 
   
        self.label_view = QLabel()
        self.label_view.setFrameShape(QFrame.Box)
        self.label_view.setFixedSize(800,600)
        
        ######### groupbox for timelapse settings
        
        self.btn_timelapse = QPushButton("start timelapse")
        self.spin_time = QSpinBox()
        self.spin_time.setRange(1,99999)
        self.combo_time_unit = QComboBox()
        self.combo_time_unit.addItems(["s","min"])
        
        self.spin_Npics = QSpinBox()
        self.spin_Npics.setRange(1,999999)
        self.spin_Npics.valueChanged.connect(self.update_totTime)
        self.spin_time.valueChanged.connect(self.update_totTime) #call after creation of btns
        self.combo_time_unit.currentIndexChanged.connect(self.update_totTime)
        
        self.lbl_totTime = QLabel()
        
        self.groupTimelapse = QGroupBox("Timelapse settings")

        self.timelapse_layout = QGridLayout()
        self.timelapse_layout.addWidget(QLabel("time step:"),0,0)
        self.timelapse_layout.addWidget(self.spin_time,0,1)
        self.timelapse_layout.addWidget(self.combo_time_unit,0,2)
        
        self.timelapse_layout.addWidget(QLabel("# of pictures:"),1,0)
        self.timelapse_layout.addWidget(self.spin_Npics,1,1)
        
        self.timelapse_layout.addWidget(self.lbl_totTime,2,0,1,2)
        self.timelapse_layout.addWidget(self.btn_timelapse,2,2,1,2)
        
        self.groupTimelapse.setLayout(self.timelapse_layout)
        
        #self.quit_button = QPushButton("Quit")
        #self.quit_button.clicked.connect(self.close)

        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.group_folder,0,0,1,2)
        self.main_layout.addWidget(self.group_cam,1,0)
        self.main_layout.addWidget(self.groupTimelapse,2,0)
        #self.main_layout.addWidget(self.quit_button,3,0)

        self.main_layout.addWidget(self.label_view,1,1,4,1)
        self.setLayout(self.main_layout)

    def on_runcam(self):
        camindex = int(self.combo_cams.currentText())
        
        resolution = [int(dim) for dim in self.combo_res.currentText().split("x")]
        
        self.camera.start(camindex, resolution)
        #self.camera.set_auto_exposure(False)
        w, h = self.camera.get_curr_resolution()
        self.label_res.setText("current: " + str(int(w)) + "x" + str(int(h)))
        self.start_live()

    def on_closecam(self):
        self.camera.close()
        self.timer.stop()
        
    def on_caminfos(self):
    
        camindices = cc.get_cams()
                       
        self.combo_cams.clear()
        for idx in camindices:
            self.combo_cams.addItem(str(idx))

    def update_camsetting(self):
        if self.camera.is_active():
            self.timer.stop()
            
            autoExp = not self.check_autoExposure.isChecked() # inverse as check means disable
            self.camera.set_auto_exposure(auto = autoExp)
            
            self.timer.start(30)
        
    def start_live(self):
        """
            Initialize camera.
        """

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """
            update pixmap of label to show current frame
        """
        frame = self.camera.get_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        image = QImage(frame, frame.shape[1], frame.shape[0], 
                       frame.strides[0], QImage.Format_RGB888)
        
        Pixmap = QPixmap.fromImage(image)
        scaledPixmap = Pixmap.scaled(self.label_view.size(), QtCore.Qt.KeepAspectRatio)
        self.label_view.setPixmap(scaledPixmap)
    
    def on_folder(self):
        folder = QFileDialog.getExistingDirectory(None, "choose output folder", self.savepath, QFileDialog.ShowDirsOnly)
        if folder != '':
            self.savepath = folder
            self.label_folder.setText(folder)

    def update_totTime(self):
        
        #calculate depending on selected unit
        deltat = self.spin_time.value()
        Npics = self.spin_Npics.value()
        
        totalt = Npics * deltat
        
        if self.combo_time_unit.currentText() == 'min':
            delta = datetime.timedelta(minutes = totalt)
        else:
            delta = datetime.timedelta(seconds = totalt)

        hours = delta.seconds//3600
        mins = (delta.seconds//60)%60
        secs = (delta.seconds%3600)%60
        deltastring = "{:02d}:{:02d}:{:02d}:{:02d}".format(delta.days,hours,mins,secs)        
        
        self.lbl_totTime.setText("<font color=\"black\">total time (dd:hh:mm:ss):</font> \
                                 <font color=\"red\" style=\"font-weight:bold\">" \
                                 + deltastring + "</font>")
    
    def closeEvent(self, event):
        """
            called before exit
        """
        self.camera.close()
        self.timer.stop()
        
    def keyPressEvent(self, e):
        #if escape is pressed, App is supposed to close
        if e.key() == Core.Qt.Key_Escape:
            self.close()
            #sys.exit(app.exec_())
            
if __name__ == '__main__':
        
    #start the application
    app = QApplication(sys.argv)
    #app.setAttribute(Core.Qt.AA_DisableHighDpiScaling)
    #app.aboutToQuit.connect(app.deleteLater)
    gui = MainApp()
    gui.show()
    sys.exit(app.exec_())