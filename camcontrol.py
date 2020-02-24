#!/usr/bin/env python

import numpy as np
import cv2

def get_cams():
    """ 
        returns list of indices of available cams
        adopted from https://stackoverflow.com/a/53310665
    """

    print("checking available cameras")
    index = 0
    camindices = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            camindices.append(index)
        cap.release()
        index += 1
    
    print("found valid camera indices:", camindices)
    return camindices
    
class camcontrol():
    """ controls camera """
    
    def __init__(self):
        self.cap = None
        self.idx = None
        self.active = False
    
    def set_idx(self, idx):
        self.idx = idx
    
    def start(self, idx, resolution = None):
        print("trying to open camera with index", idx, "and resolution", resolution)
        
        self.set_idx(idx)
        self.cap = cv2.VideoCapture(self.idx)
        
        if resolution is not None:
            w, h = resolution[0], resolution[1]
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        
        self.active = True
        
    def is_active(self):
        return self.active
    
    def get_frame(self):
        ret, frame = self.cap.read()
        return frame
        
    def close(self):
        if self.active == True:
            self.cap.release()
            self.cap = None
            self.active = False
    
    def get_curr_resolution(self):
        
        if self.is_active():
            w, h = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            return w,h
        else:
            raise Exception("no capture device currently open")
    
    def set_auto_exposure(self, auto = False):
        """https://stackoverflow.com/questions/53545945/how-to-set-camera-to-auto-exposure-with-opencv-3-4-2"""
        if auto == True:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
            print("enabling auto exposure")
        elif auto == False:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            print("disabling auto exposure")
            
    def set_brightness(brightness):
        pass