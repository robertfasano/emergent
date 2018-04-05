from labAPI import gui, lattice_client
from threading import Thread
import json
class Setpoint():
    def __init__(self, name, tab, value, row, col, width = 1):
        self.tab = tab
        self.name = name
        self.label = self.tab._addLabel(self.name, row, col, width = width, style = self.tab.panel.styleUnlock)
        self.value = self.tab._addEdit(str(value), row,col+1 + width-1)

class LasersTab(gui.Tab):
    def __init__(self, panel, clock):
        super().__init__('Lattice', panel)
        self.panel = panel
        adc_id = {'0': None, '1':'1C2678C', '2':'1C26788'}[clock]
        self.frequency = {}
        self.offset = 2082844800 - 3437602072
        self.adc = self.panel.monitorTab.ADCs[adc_id]
        
        self.client = lattice_client.Client(adc = self.adc)
        self.client.connect()
            
        self.parameters = {}
        self.parameters['Etalon'] = {'Tuning step':.1, 'Tuning delay': .5, 'Tuning threshold':.5, 'Lock threshold':1.5}
        self.parameters['PZT'] = {'Tuning step': .5, 'Tuning delay': .5, 'Tuning threshold': 0.01}
        self.parameters['Acquisition'] = {'Transmission threshold': 0.6, 'Sweep steps':60, 'Sweep range': 0.15}
        self.parameters['Slow'] = {'Gain': 0.001, 'Center threshold': .4}
        
        self.setpoints = {}
        self.setpoints['Etalon'] = {}
        self.setpoints['PZT'] = {}
        self.setpoints['Acquisition'] = {}
        self.setpoints['Slow'] = {}
        
        col = 0
        row = 0
        for x in ['Etalon', 'Slow']:
            self._addLabel(x, row, col, width = 1)
            row += 1
            for p in self.parameters[x]:
                self.setpoints[x][p] = Setpoint(p, self, self.parameters[x][p], row, col, width = 2)
                row += 1 
                
        col = 3
        row = 0
        for x in ['PZT', 'Acquisition']:
            self._addLabel(x, row, col, width = 1)
            row += 1
            for p in self.parameters[x]:
                self.setpoints[x][p] = Setpoint(p, self, self.parameters[x][p], row, col, width = 2)
                row += 1
        
        self._addButton('Connect', self.client.connect, row+3, 0, style = self.panel.styleUnlock)

        self._addButton('Lock', self.lock, row+3, 2, style = self.panel.styleUnlock)
        self._addButton('Ping', self.ping, row+3, 1, style = self.panel.styleUnlock)
        self._addButton('Abort', self.abort, row+3, 3, style = self.panel.styleUnlock)
        
        ''' Wavemeter '''
        with open(panel.filepath['Lasers']) as file:
            j = json.load(file)
            
        channels = []
        for channel in j['Wavemeter']:
            channels.append(j['Wavemeter'][channel]['Name'])
        self.wavemeterLabel = self._addLabel('Not connected', row+3, 5)
#        self.wavemeterComboBox = self._addComboBox(channels, row+3, 3,width=1, height=1)
#        self.wavemeterComboBox.activated.connect(self.select_channel)
        
    def abort(self):
        self.client.abort = 1
        
    def lock(self):
        self.panel.threads['Saving'] = 0
        self.panel.monitorTab.saveButton.setStyleSheet(self.panel.styleUnlock)
        for x in self.parameters:
            for p in self.parameters[x]:
                self.parameters[x][p] = float(self.setpoints[x][p].value.text())
            
        print(self.parameters)
        self.thread = Thread(target=self.client.lock, args=(self.parameters,))
        self.panel.threads['Lattice lock'] = 1
        self.thread.start()
        
    def ping(self):
        return self.client.ping()
    
    def select_channel(self):
        choice = self.wavemeterComboBox.currentText()
        self.channel = choice[3]
        
    def stream_frequency(self):
        self.client.message(op = 'stream_frequency')
        while self.panel.threads['Wavemeter']:
            self.frequency[self.channel] = self.client.message(op = 'request')
            self.wavemeterEdit.setText(str(self.frequency[self.channel]))
        self.client.message(op = 'done')
            
    def write_queue(self):
        while self.panel.threads['Wavemeter']:
            try:
                self.logfile.write(self.queue[0])
                self.logfile.flush()
                del self.logqueue[0]
            except:
                continue