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
import tifffile
import camcontrol as cc
import glob

class MainApp(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.setup_ui()
        
        self.update_totTime()
        self.timer = QTimer()
        self.camera = cc.camcontrol()
        self.snapindex = None
        
        self.savepath = os.getcwd()
        self.get_snapindex()
        self.set_folderlabel(self.savepath)
        self.on_caminfos()

    def setup_ui(self):
        """Initialize widgets.
        """
        
        self.setWindowTitle("Campy")
        
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
        self.btn_closecam.setEnabled(False)
        
        self.btn_snapsingle = QPushButton("snap single image")
        self.btn_snapsingle.clicked.connect(self.on_snapsingle)
        self.btn_snapsingle.setEnabled(False)
        
        # enabling of auto exposure with cv2 not working so far...
        #self.check_autoExposure = QCheckBox("disable auto-brightness")
        #self.check_autoExposure.stateChanged.connect(self.update_camsetting)
        
        self.slider_exposure = QSlider(Qt.Horizontal)
        self.slider_exposure.setMaximum(0)
        self.slider_exposure.setMinimum(-15)
        self.slider_exposure.setValue(-3)
        self.slider_exposure.valueChanged.connect(self.on_change_exposure)
        
        self.group_cam = QGroupBox("Camera settings")
        self.layout_group_cam = QGridLayout()
        self.layout_group_cam.addWidget(QLabel("camera index:"),0,0)
        self.layout_group_cam.addWidget(self.combo_cams,0,1)
        self.layout_group_cam.addWidget(QLabel("resolution:"),1,0)
        self.layout_group_cam.addWidget(self.combo_res,1,1)
        self.layout_group_cam.addWidget(self.label_res,1,2)
        self.layout_group_cam.addWidget(self.btn_caminfos,0,2)
        self.layout_group_cam.addWidget(QLabel("exposure:"),2,0)
        self.layout_group_cam.addWidget(self.slider_exposure,2,1,1,2)
        self.layout_group_cam.addWidget(self.btn_runcam,3,0)
        self.layout_group_cam.addWidget(self.btn_closecam,3,1)
        self.layout_group_cam.addWidget(self.btn_snapsingle,3,2)
        self.group_cam.setLayout(self.layout_group_cam)
        
        ######### used for display images 
   
        self.label_view = QLabel()
        self.label_view.setFrameShape(QFrame.Box)
        self.label_view.setFixedSize(800,600)
        
        ######### groupbox for timelapse settings
        
        self.btn_timelapse = QPushButton("start timelapse")
        self.btn_timelapse.setEnabled(False)
        self.btn_timelapse.clicked.connect(self.on_timelapse)
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
        
        self.btn_stop_timelapse = QPushButton("stop")
        self.btn_stop_timelapse.clicked.connect(self.stop_timelapse)
        self.btn_stop_timelapse.setEnabled(False)
        
        self.prog_timelapse = QProgressBar()
        self.prog_timelapse.setTextVisible(False)
        self.label_Ntimelapse = QLabel("")
        
        self.groupTimelapse = QGroupBox("Timelapse settings")

        self.timelapse_layout = QGridLayout()
        self.timelapse_layout.addWidget(QLabel("time step:"),0,0)
        self.timelapse_layout.addWidget(self.spin_time,0,1)
        self.timelapse_layout.addWidget(self.combo_time_unit,0,2)
        
        self.timelapse_layout.addWidget(QLabel("# of pictures:"),1,0)
        self.timelapse_layout.addWidget(self.spin_Npics,1,1)
        
        self.timelapse_layout.addWidget(self.lbl_totTime,2,0,1,2)
        self.timelapse_layout.addWidget(self.btn_timelapse,2,2,1,1)

        self.layout_timelapse_progress = QHBoxLayout()
        self.layout_timelapse_progress.addWidget(self.prog_timelapse)#, stretch=1)
        self.layout_timelapse_progress.addWidget(self.label_Ntimelapse)
        
        self.timelapse_layout.addLayout(self.layout_timelapse_progress,3,0,1,2)
        self.timelapse_layout.addWidget(self.btn_stop_timelapse,3,2)
        
        self.groupTimelapse.setLayout(self.timelapse_layout)
        
        #self.quit_button = QPushButton("Quit")
        #self.quit_button.clicked.connect(self.close)

        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.group_folder,0,0)
        self.main_layout.addWidget(self.group_cam,1,0)
        self.main_layout.addWidget(self.groupTimelapse,2,0)
        #self.main_layout.addWidget(self.quit_button,3,0)

        self.main_layout.addWidget(self.label_view,0,1,4,1)
        self.setLayout(self.main_layout)

        self.setFixedSize(self.sizeHint()) # lock size of window
        
    def on_runcam(self):

        # disable buttons
        #camwidgets=self.group_cam.findChildren(QWidget) iterate over widgets or specify:
        self.slider_exposure.setEnabled(True)
        self.combo_cams.setEnabled(False)
        self.btn_runcam.setEnabled(False)
        self.btn_caminfos.setEnabled(False)
        self.combo_res.setEnabled(False)
        
        self.btn_closecam.setEnabled(True)
        self.btn_snapsingle.setEnabled(True)
        self.btn_timelapse.setEnabled(True)
        
        camindex = int(self.combo_cams.currentText())
        
        resolution = [int(dim) for dim in self.combo_res.currentText().split("x")]
        
        self.camera.start(camindex, resolution)
        
        w, h = self.camera.get_curr_resolution()
        self.label_res.setText("current: " + str(int(w)) + "x" + str(int(h)))
        self.start_live()
        self.on_change_exposure()

    def on_closecam(self):    
        self.camera.close()
        self.timer.stop()
        
        # enable buttons
        camwidgets=self.group_cam.findChildren(QWidget)
        for widget in camwidgets:
           widget.setEnabled(True)
        self.btn_snapsingle.setEnabled(False)
        self.btn_closecam.setEnabled(False)
        self.btn_timelapse.setEnabled(False)
        
    def on_caminfos(self):
    
        camindices = cc.get_cams()
                       
        self.combo_cams.clear()
        for idx in camindices:
            self.combo_cams.addItem(str(idx))

    """
    def update_camsetting(self):
        if self.camera.is_active():
            self.timer.stop()
            
            autoExp = not self.check_autoExposure.isChecked() # inverse as check means disable
            self.camera.set_auto_exposure(auto = autoExp)
            
            self.timer.start(30)
    """
        
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
        if frame is not None:

            #frame = cv2.Canny(frame, 25, 75)
            #print(frame.shape)
            format = QImage.Format_RGB888
            #format = QImage.Format_Mono            
            frame = cv2.flip(frame, 1)
            
            image = QImage(frame, frame.shape[1], frame.shape[0], 
                           frame.strides[0], format)
            
            Pixmap = QPixmap.fromImage(image)
            scaledPixmap = Pixmap.scaled(self.label_view.size(), QtCore.Qt.KeepAspectRatio)
            self.label_view.setPixmap(scaledPixmap)

    
    def on_folder(self):
        folder = QFileDialog.getExistingDirectory(None, "choose output folder", self.savepath, QFileDialog.ShowDirsOnly)
        if folder != '':
            self.savepath = folder
            self.set_folderlabel(folder)
            self.get_snapindex()

    def set_folderlabel(self, folder):
        if len(folder) > 45:
            displayfolder = folder[0:12] + "..." + folder[-30:]
            self.label_folder.setText(displayfolder)   
        else:
            self.label_folder.setText(folder)

    def on_change_exposure(self):
        if self.camera.is_active():
            self.timer.stop()
            
            exp = self.slider_exposure.value()
            self.camera.set_exposure(exposure = exp)
            self.timer.start(30)        

    def on_snapsingle(self):
        if self.camera.is_active():
            self.timer.stop()
            
            frame = self.camera.get_frame()
            indexstr = "{:03d}".format(self.snapindex)      
            tifffile.imwrite(self.savepath + '\\snap_' + indexstr + '.tif', frame, photometric='rgb')  
            self.snapindex = self.snapindex + 1
            
            self.timer.start(30)          

    def get_snapindex(self):
        """ looks through files in outputfolder to get highest index """
        files = glob.glob(self.savepath + '\\*.tif')
        snaps = [file for file in files if "snap_" in file] #remove all files which are not called snap_####
        indices = [int(file.split("snap_")[1].split(".tif")[0]) for file in snaps]
        
        if len(indices) == 0:
            self.snapindex = 0
        else:
            self.snapindex = max(indices) + 1

    def on_timelapse(self):
        # lock selected input, can be definitely improved...
        self.btn_folder.setEnabled(False)
        self.btn_stop_timelapse.setEnabled(True)
        self.slider_exposure.setEnabled(False)
        self.btn_timelapse.setEnabled(False)
        self.spin_Npics.setEnabled(False)
        self.spin_time.setEnabled(False)
        self.combo_time_unit.setEnabled(False)
        self.btn_snapsingle.setEnabled(False)
        self.btn_closecam.setEnabled(False)
        
        starttime = datetime.datetime.now()
        foldername = "TL_" + starttime.strftime("%Y-%m-%d_%H-%M-%S") # include also timestep?
        self.path_timelapse = self.savepath+"\\"+foldername
        
        os.mkdir(self.path_timelapse)
        
        self.start_timelapse()

    def start_timelapse(self):
        """ sets timelapse values and starts timer for periodic image capture """
    
        self.i_timelapse = 0        
        self.N_timelapse = self.spin_Npics.value() # don't forget to lock gui elements...
        self.N_timelapse_digits = len(str(self.N_timelapse))
        self.prog_timelapse.setRange(0,self.N_timelapse)
        
        deltat = self.spin_time.value()       
        if self.combo_time_unit.currentText() == 'min':
            delta_millis = deltat * 60000
        else:
            delta_millis = deltat * 1000
        
        self.timer_timelapse = QTimer() # keep in mind: old timer is still running
        self.timer_timelapse.timeout.connect(self.update_timelapse)
        self.timer_timelapse.start(delta_millis)
        self.update_timelapse() # execute once directly after start, 
                                # otherwise first picture will be only taken after waiting for first period

    def stop_timelapse(self):
        self.timer_timelapse.stop()
        
        # unlock gui elements
        self.slider_exposure.setEnabled(True)
        self.btn_folder.setEnabled(True)
        self.btn_stop_timelapse.setEnabled(False)
        self.slider_exposure.setEnabled(True)
        self.btn_timelapse.setEnabled(True)
        self.spin_Npics.setEnabled(True)
        self.spin_time.setEnabled(True)
        self.combo_time_unit.setEnabled(True)
        self.btn_snapsingle.setEnabled(True)
        self.btn_closecam.setEnabled(True)
        
    def update_timelapse(self):
        """ callback for timer during timelapse to take new image """        
        
        self.prog_timelapse.setValue(self.i_timelapse+1)
        self.label_Ntimelapse.setText(str(self.i_timelapse+1).zfill(self.N_timelapse_digits)+"/"+str(self.N_timelapse))
        frame = self.camera.get_frame()   
        tifffile.imwrite(self.path_timelapse + '\\' + "{:06d}".format(self.i_timelapse) + '.tif', frame, photometric='rgb')  
        self.i_timelapse = self.i_timelapse + 1
        if self.i_timelapse >= self.N_timelapse:
            self.stop_timelapse()

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
            
if __name__ == '__main__':
        
    #start the application
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    gui = MainApp()
    gui.show()
    sys.exit(app.exec_())