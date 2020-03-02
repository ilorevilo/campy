# Campy
Simple gui written in Python using PyQt5 and OpenCV for displaying and controlling arbitrary (Web-, USB-) Cameras.
Can be i.a. used to control a USB-Microscope and record images as .tif-files.
Offers a timelapse mode where images are recorded in specified time intervals.

https://github.com/ilorevilo/campy

![gui-sample](/gui-sample.PNG)

### Running Campy 
* make sure you have installed PyQt5, OpenCV3 and tifffile (tested with python=3.7.4, pyqt=5.9.2, py-opencv=3.4.2, tifffile=2020.2.16)
* OR create a new conda environmend from provided [campy.yml](campy.yml) by `conda env create -f campy.yml`
* then run `python campy-gui.py` to start gui

### Bugs/ Issues
* camera exposure is controlled only manually so far, re-enabling auto exposure via `self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)` does not work, so it's not implemented

### License
Check [LICENSE](LICENSE) for details