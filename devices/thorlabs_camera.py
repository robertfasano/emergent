from instrumental import instrument, list_instruments, Q_
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import gridspec
import numpy as np
import time
from threading import Thread
from matplotlib.colors import LogNorm
import pint


#paramsets = list_instruments()
#camera = instrument(paramsets[0])
#camera.save_instrument('camera')

#camera = instrument('camera')
#camera.start_live_video()


class ThorlabsCamera():
    def __init__(self):
        ureg = pint.UnitRegistry()
        self.camera = instrument('camera')
        self.camera.start_live_video(gain=100, exposure_time = Q_('90 ms'))
#        self.camera.start_live_video()

        self.background = self.camera.latest_frame()
        self.num_points = 50
        self.fluorescence = []
        
        self.max = 250
        self.min = 140
        
    def capture_video(self):
        self.fig = plt.figure()
        gs  = gridspec.GridSpec(2, 1, height_ratios=[3,1])

#        self.fig, (self.ax1, self.ax2) = plt.subplots(2,1)
        self.ax1 = plt.subplot(gs[0])
        self.ax2 = plt.subplot(gs[1])
        self.ax2.get_yaxis().set_visible(False)
        self.ax2.get_xaxis().set_visible(False)

        self.video_image = self.ax1.imshow(self.camera.latest_frame(), animated=True, cmap='rainbow')
        self.video_animation = animation.FuncAnimation(self.fig, self.update_video, interval=1, blit=True)
        self.video_fluorescence = animation.FuncAnimation(self.fig, self.update_fluorescence, interval=1, blit=True)

        plt.show()
    
    def update_fluorescence(self, *args):
        self.ax2.cla()
        self.line = self.ax2.plot(self.fluorescence, 'k')

        return self.line
    
    def update_video(self, *args):
        frame = self.camera.latest_frame() 
        frame[np.where(frame<self.min)] = 0
        frame[np.where(frame>self.max)] = 0
        f = np.sum(frame)
        self.video_image.set_array(frame)
        self.fluorescence.append(f)
        if len(self.fluorescence) > self.num_points:
            del self.fluorescence[0]

        return self.video_image,

c = ThorlabsCamera()
c.capture_video()