
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QMenu, QAction,
        QWidget, QCheckBox, QHBoxLayout, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from emergent.modules.units import Units

class ttlLabel(QLabel):
    def __init__(self, name, channel, grid):
        super().__init__(name)
        self.name = name
        self.channel = channel
        self.grid = grid
        self.customContextMenuRequested.connect(self.openMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def openMenu(self, pos):
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()
        options = {'Set all high': self.set_all_high,
                   'Set all low': self.set_all_low}
        actions = {}

        for option in options:
            actions[option] = QAction(option, self)
            actions[option].triggered.connect(options[option])
            menu.addAction(actions[option])
        selectedItem = menu.exec_(globalPos)

    def set_all_high(self):
        steps = self.grid.get_sequence()
        for step in steps:
            if self.channel not in step['TTL']:
                step['TTL'].append(self.channel)

        self.grid.dashboard.post('hubs/%s/sequencer/sequence'%self.grid.hub, steps)
        current_step = self.grid.dashboard.get('hubs/%s/sequencer/current_step'%self.grid.hub)
        self.grid.dashboard.post('hubs/%s/sequencer/current_step'%self.grid.hub, {'step': current_step})
        self.grid.redraw(steps)

    def set_all_low(self):
        steps = self.grid.get_sequence()
        for step in steps:
            step['TTL'] = [x for x in step['TTL'] if x != self.channel]

        self.grid.dashboard.post('hubs/%s/sequencer/sequence'%self.grid.hub, steps)
        current_step = self.grid.dashboard.get('hubs/%s/sequencer/current_step'%self.grid.hub)
        self.grid.dashboard.post('hubs/%s/sequencer/current_step'%self.grid.hub, {'step': current_step})
        self.grid.redraw(steps)

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

class DACEdit(QLineEdit):
    def __init__(self, name, text, dashboard, hub, grid):
        super().__init__(text)
        self.picklable = False
        self.dashboard = dashboard
        self.grid = grid
        self.hub = hub
        self.name = name
        self.returnPressed.connect(self.onReturn)
        self.setMaximumWidth(75)
        self.setFixedWidth(75)
        self.unit_parser = Units()

    def onReturn(self):
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
            name = str(ttl)
            if type(self.ttls) is dict:
                name += ': %s'%str(self.ttls[ttl])
            self.grid_layout.addWidget(ttlLabel(name, channel=ttl, grid=self), row, 0)
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

        ''' Create DAC labels '''
        self.dacs = self.dashboard.get('hubs/%s/sequencer/dac'%hub)
        label = BoldLabel('DAC')
        label.setBold(True)
        self.grid_layout.addWidget(label, row, 0)
        row += 1
        for dac in self.dacs:
            self.grid_layout.addWidget(QLabel(str(dac)), row, 0)
            row += 1
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
        self.dashboard.sequence_update_signal.connect(self.refresh)

    def refresh(self):
        timesteps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        self.redraw(timesteps)

    def draw(self, sequence):
        self.labels = {}
        self.step_edits = {}
        self.checkboxes = {}
        self.adc_checkboxes = {}
        self.dac_edits = {}
        col = 1
        for step in sequence:
            row = self.add_step(step, col)
            col += 1
        total_cycle_time = self.get_cycle_time()*1000
        self.total_time_label = QLabel('%.1f ms'%total_cycle_time)
        self.grid_layout.addWidget(QLabel('Cycle time:'), row, 0)
        self.grid_layout.addWidget(self.total_time_label, row, 1)
        self.bold_active_step()

    def redraw(self, sequence):
        for step in self.labels:
            self.remove_step(step)
        self.grid_layout.removeWidget(self.total_time_label)
        self.total_time_label.deleteLater()
        self.draw(sequence)
        QApplication.processEvents()        # determine new minimumSize
        self.resize(self.minimumSize())

    def get_cycle_time(self):
        T = 0
        for edit in self.step_edits.values():
            T += float(edit.text())
        return T

    def get_sequence(self):
        sequence = []
        for name in self.labels:
            new_step = {}
            new_step['duration'] = self.step_edits[name].text()
            new_step['name'] = name
            new_step['TTL'] = []
            new_step['ADC'] = []
            new_step['DAC'] = {}
            for ttl in self.ttls:
                if self.checkboxes[name][ttl].isChecked():
                    new_step['TTL'].append(ttl)
            for adc in self.adcs:
                if self.adc_checkboxes[name][adc].isChecked():
                    new_step['ADC'].append(adc)
            for dac in self.dacs:
                new_step['DAC'][int(dac)] = float(self.dac_edits[name][dac].text())
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

        ''' Add DAC edits '''
        self.dac_edits[name] = {}
        row += 1
        for dac in self.dacs:
            if int(dac) in step['DAC']:
                value = step['DAC'][int(dac)]
            elif str(dac) in step['DAC']:
                value = step['DAC'][str(dac)]
            else:
                value = 0
            edit = DACEdit(str(dac), str(value), self.dashboard, self.hub, self)
            self.grid_layout.addWidget(edit, row, col)
            self.dac_edits[name][dac] = edit
            row += 1
        return row

    def remove_step(self, step):
        remove = [self.labels[step], self.step_edits[step]]
        for switch in self.ttls:
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

        total_cycle_time = self.get_cycle_time()*1000
        self.total_time_label.setText('%.1f ms'%total_cycle_time)
