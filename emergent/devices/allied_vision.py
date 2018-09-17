from pymba import *
import time, cv2
import numpy as np
import matplotlib.pyplot as plt

class Mako():
    def __init__(self):
        self.vimba = Vimba()
        self.vimba.startup()

        system = vimba.getSystem()
        # list available cameras (after enabling discovery for GigE cameras)
        if system.GeVTLIsPresent:
            system.runFeatureCommand("GeVDiscoveryAllOnce")
            time.sleep(0.2)
        cameraIds = self.vimba.getCameraIds()
        for cameraId in cameraIds:
            print('Camera ID:', cameraId)
        # get and open a camera
        self.camera = self.vimba.getCamera(cameraIds[0])
        self.camera.openCamera()
        self.camera.AcquisitionMode = 'Continuous'
        self.frame = self.camera.getFrame()    # creates a frame
        self.frame.announceFrame()

        self.camera.startCapture()
        self.frame.queueFrameCapture()
        self.camera.runFeatureCommand('AcquisitionStart')

    def get_frame(self):
        self.frame.waitFrameCapture(1000)
        self.frame.queueFrameCapture()
        imgData = self.frame.getBufferByteData()

        img = np.ndarray(buffer = imgData,
                                       dtype = np.uint8,
                                       shape = (self.frame.height,
                                                self.frame.width,
                                                1))
        minPixel = 0
        maxPixel = 127
        img = np.clip(img, 0,maxPixel)
        img *= int(255.0/maxPixel)
        img = cv2.applyColorMap(img, cv2.COLORMAP_JET)

        img = cv2.resize(img,(960,540))
        cv2.imshow("im",img)

    def shutdown(self):
        self.frame.waitFrameCapture(1000)
        self.camera.runFeatureCommand('AcquisitionStop')
        self.camera.endCapture()
        self.camera.revokeAllFrames()

        self.vimba.shutdown()
        self.cv2.destroyAllWindows()

if __name__ == '__main__':
    camera = Mako()
