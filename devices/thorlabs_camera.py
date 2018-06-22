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

def get_image(ax = None):
    n_frames = 10
    image = camera.grab_image(n_frames=n_frames)
    if n_frames > 1:
        img = image[0]
        for i in range(1,n_frames):
            img += image[i]
    else:
        img = image
        
    if ax == None:
        fig = plt.figure()
        ax = fig.gca()
    ax.imshow(img)
    plt.pause(0.05)
    plt.show()
    
    return ax

class ThorlabsCamera():
    def __init__(self):
        ureg = pint.UnitRegistry()
        self.camera = instrument('camera')
        self.camera.start_live_video(gain=100, exposure_time = Q_('10 ms'))
        self.background = self.camera.latest_frame()
        self.num_points = 50
        self.fluorescence = []
        
    def capture_video(self):
        self.fig = plt.figure()
        gs  = gridspec.GridSpec(2, 1, height_ratios=[3,1])

#        self.fig, (self.ax1, self.ax2) = plt.subplots(2,1)
        self.ax1 = plt.subplot(gs[0])
        self.ax2 = plt.subplot(gs[1])
        self.ax2.get_yaxis().set_visible(False)
        self.ax2.get_xaxis().set_visible(False)

        self.video_image = self.ax1.imshow(self.camera.latest_frame(), animated=True, cmap='gray', norm=LogNorm(vmin=0.0001, vmax=255))
        self.video_animation = animation.FuncAnimation(self.fig, self.update_video, interval=1, blit=True)
        self.video_fluorescence = animation.FuncAnimation(self.fig, self.update_fluorescence, interval=1, blit=True)

        plt.show()
    
    def update_fluorescence(self, *args):
        self.ax2.cla()
        self.line = self.ax2.plot(self.fluorescence, 'k')

        return self.line
    
    def update_video(self, *args):
        frame = self.camera.latest_frame() #- self.background
#        frame = np.maximum(frame, 0)
#        frame = frame * 2
        min_pixel = np.min(frame)
        max_pixel = np.max(frame)
#        print(max_pixel)
        f = np.sum(frame)
        self.video_image.set_array(frame)
#        print(f)
        self.fluorescence.append(f)
        if len(self.fluorescence) > self.num_points:
            del self.fluorescence[0]
#        self.ax2.plot(self.fluorescence, 'k')
#        plt.pause(0.001)

        return self.video_image,

c = ThorlabsCamera()
c.capture_video()