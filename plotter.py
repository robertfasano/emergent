import numpy as np
import matplotlib.pyplot as plt

def drawPlot(self,choice, df, ):   
    ''' Linked to the dropdown menu for ADC input choice; plots the user choice on the display 
        
        Arguments: 
            choice (str): the user-chosen value of the dropdown menu
        Returns:
            widget: 
    '''    
    # define viewbox for mouse drag zooming
    vb = CustomViewBox()
    widget = pg.PlotWidget(viewBox=vb)
    try:
        widget.plot(df.index,df[choice].values, clear=True, title=choice)
        return widget
    except Exception:
        return 
#    coords = [1, 6, 5, 2]
#        self.tabMonitor.layout.addWidget(self.dataPlotterWidget,coords[0], coords[1], coords[2], coords[3])

    
    
    