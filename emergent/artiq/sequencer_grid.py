
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit,
        QWidget, QCheckBox, QHBoxLayout, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from emergent.modules.units import Units

class StateCheckbox(QCheckBox):
    def __init__(self, name, timestep, state, dashboard, hub, grid):
        super().__init__()
        self.name = name
        self.timestep = timestep
        self.dashboard = dashboard
        self.grid = grid
        self.hub = hub
        self.picklable = False
        self.setChecked(state)
        self.stateChanged.connect(self.onChanged)

    def onChanged(self, state):
        sequence = self.grid.get_sequence()
        params = {'hub': self.hub}
        self.dashboard.post('hubs/%s/sequencer/sequence'%self.hub, sequence)
        current_step = self.dashboard.get('hubs/%s/sequencer/current_step'%self.hub)
        if current_step == self.name:
            self.dashboard.post('hubs/%s/sequencer/current_step'%self.hub, {'step': self.name})

class StepEdit(QLineEdit):
    def __init__(self, name, text, dashboard, hub):
        super().__init__(text)
        self.picklable = False
        self.dashboard = dashboard
        self.hub = hub
        self.name = name
        self.returnPressed.connect(self.onReturn)
        self.setMaximumWidth(75)
        self.setFixedWidth(75)
        self.unit_parser = Units()
        
    def onReturn(self):
        text = self.text()
        ''' Unit comprehension '''
        if ' ' in text:
            value = text.split(' ')[0]
            unit = text.split(' ')[1]
            value = float(value)*self.unit_parser.get_scaling(unit)
        else:
            value = float(text)
        state = {'sequencer':{self.name: value}}
        self.dashboard.post('hubs/%s/state'%self.hub, state)
        self.dashboard.actuate_signal.emit({self.hub: state})

class BoldLabel(QLabel):
    def __init__(self, name):
        super().__init__(name)
        self.name = name

    def setBold(self, bold):
        if bold:
            self.setText('<b>'+self.name+'</b>')
        else:
            self.setText(self.name)

class GridWindow(QWidget):
    def __init__(self, dashboard, hub):
        super(GridWindow, self).__init__(None)
        with open('dashboard/gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('Timing grid')
        self.setObjectName('timingGrid')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding);
        self.dashboard = dashboard
        self.hub = hub
        self.picklable = False

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.widget = QWidget()
        self.grid_layout = QGridLayout()
        self.widget.setLayout(self.grid_layout)
        self.layout.addWidget(self.widget)

        ''' Create TTL labels '''
        self.ttls = self.dashboard.get('hubs/%s/sequencer/ttl'%hub)
        label = BoldLabel('TTL')
        label.setBold(True)
        self.grid_layout.addWidget(label, 2, 0)
        row = 3


        for ttl in self.ttls:
            label = str(ttl)
            if type(self.ttls) is dict:
                label += ': %s'%str(self.ttls[ttl])
            self.grid_layout.addWidget(QLabel(label), row, 0)
            row += 1

        ''' Create ADC labels '''
        self.adcs = self.dashboard.get('hubs/%s/sequencer/adc'%hub)
        label = BoldLabel('ADC')
        label.setBold(True)
        self.grid_layout.addWidget(label, row, 0)
        row += 1
        for adc in self.adcs:
            label = str(adc)
            if type(self.adcs) is dict:
                label += ': %s'%str(self.adcs[adc])
            self.grid_layout.addWidget(QLabel(label), row, 0)
            row += 1

        # ''' Create DAC labels '''
        # self.dacs = self.dashboard.get('hubs/%s/sequencer/dac'%hub)
        # self.grid_layout.addWidget(QLabel('DAC'), row, 0)
        # row += 1
        # for dac in self.dacs:
        #     self.grid_layout.addWidget(QLabel(str(dac)), row, 0)
        #     row += 1
        #
        # ''' Create DDS labels '''
        # self.dds = self.dashboard.get('hubs/%s/sequencer/dds'%hub)
        # self.grid_layout.addWidget(QLabel('DDS'), row, 0)
        # row += 1
        # for dds in self.dds:
        #     self.grid_layout.addWidget(QLabel(str(dds)), row, 0)
        #     row += 1

        timesteps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        self.draw(timesteps)

        self.dashboard.actuate_signal.connect(self.actuate)
        self.dashboard.timestep_signal.connect(self.bold_active_step)

    def draw(self, sequence):
        self.labels = {}
        self.step_edits = {}
        self.checkboxes = {}
        self.adc_checkboxes = {}
        col = 1
        for step in sequence:
            self.add_step(step, col)
            col += 1
        self.bold_active_step()

    def redraw(self, sequence):
        for step in self.labels:
            self.remove_step(step)
        self.draw(sequence)
        QApplication.processEvents()        # determine new minimumSize
        self.resize(self.minimumSize())

    def get_sequence(self):
        sequence = []
        for name in self.labels:
            new_step = {}
            new_step['duration'] = self.step_edits[name].text()
            new_step['name'] = name
            new_step['TTL'] = []
            new_step['ADC'] = []
            for ttl in self.ttls:
                if self.checkboxes[name][ttl].isChecked():
                    new_step['TTL'].append(ttl)
            for adc in self.adcs:
                if self.adc_checkboxes[name][adc].isChecked():
                    new_step['ADC'].append(adc)
            sequence.append(new_step)
        return sequence

    def add_step(self, step, col):
        name = step['name']
        ''' Add label and edit '''
        self.labels[name] = BoldLabel(name)
        self.grid_layout.addWidget(self.labels[name], 0, col)
        self.step_edits[name] = StepEdit(name, str(step['duration']), self.dashboard, self.hub)
        self.grid_layout.addWidget(self.step_edits[name], 1, col)

        ''' Add TTL checkboxes '''
        row = 3
        self.checkboxes[name] = {}
        for switch in self.ttls:
            state = 0
            if int(switch) in step['TTL'] or str(switch) in step['TTL']:
                state = 1
            box = StateCheckbox(name, step, state, self.dashboard, self.hub, self)
            self.grid_layout.addWidget(box, row, col)
            self.checkboxes[name][switch] = box
            row += 1

        ''' Add ADC checkboxes '''
        self.adc_checkboxes[name] = {}
        row += 1
        for adc in self.adcs:
            state = 0
            if int(adc) in step['ADC'] or str(adc) in step['ADC']:
                state = 1
            box = StateCheckbox(name, step, state, self.dashboard, self.hub, self)
            self.grid_layout.addWidget(box, row, col)
            self.adc_checkboxes[name][adc] = box
            row += 1

    def remove_step(self, step):
        remove = [self.labels[step], self.step_edits[step]]
        for switch in self.switches:
            remove.append(self.checkboxes[step][switch])
        for widget in remove:
            self.grid_layout.removeWidget(widget)
            widget.deleteLater()

    def bold_active_step(self, current_step=None):
        steps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        if current_step is None:
            current_step = self.dashboard.get('hubs/%s/sequencer/current_step'%self.hub)
        else:
            current_step = current_step['name']
        for step in steps:
            if step['name'] == current_step:
                self.labels[step['name']].setBold(True)
            else:
                self.labels[step['name']].setBold(False)

    def actuate(self, state):
        try:
            state = state[self.hub]['sequencer']
        except KeyError:
            return
        for step_name in self.step_edits:
            if step_name in state:
                self.step_edits[step_name].setText(str(state[step_name]))
