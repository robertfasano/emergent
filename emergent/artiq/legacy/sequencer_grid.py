
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QMenu, QAction, QPushButton,
        QWidget, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from emergent.utilities.units import Units
import time
import numpy as np
from emergent.artiq.sequencer_table import SequencerTable

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

class StepLabel(BoldLabel):
    def __init__(self, name, grid):
        super().__init__(name)
        self.grid = grid
        self.customContextMenuRequested.connect(self.openMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def openMenu(self, pos):
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()
        move_menu = menu.addMenu('Move')

        move_options = {'Left': self.move_left,
                   'Right': self.move_right }
        actions = {}

        for option in move_options:
            actions[option] = QAction(option, self)
            actions[option].triggered.connect(move_options[option])
            move_menu.addAction(actions[option])
        selectedItem = menu.exec_(globalPos)

    def move_left(self):
        self.grid.move(self.name, -1)

    def move_right(self):
        self.grid.move(self.name, 1)



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
        self.dashboard.test_signal.connect(lambda: self.insert_step('test', 0))
        # self.dashboard.test_signal.connect(lambda: self.swap_timesteps('load', 'probe'))

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.selector_layout = QHBoxLayout()
        self.sequence_selector = QComboBox()
        for item in self.dashboard.get('hubs/%s/sequencer/sequences'%self.hub):
            self.sequence_selector.addItem(item)
        self.sequence_selector.currentTextChanged.connect(self.activate)
        self.selector_layout.addWidget(self.sequence_selector)
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete)
        self.selector_layout.addWidget(self.delete_button)
        self.layout.addLayout(self.selector_layout)


        self.store_layout = QHBoxLayout()
        self.store_edit = QLineEdit('Enter name here')
        self.store_layout.addWidget(self.store_edit)
        self.store_button = QPushButton('Store')
        self.store_button.clicked.connect(self.store)
        self.store_layout.addWidget(self.store_button)
        self.layout.addLayout(self.store_layout)

        self.widget = QWidget()
        self.grid_layout = QGridLayout()
        self.widget.setLayout(self.grid_layout)
        self.layout.addWidget(self.widget)


        # self.add_table()
        self.add_labels()
        timesteps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        self.draw(timesteps)

        self.dashboard.actuate_signal.connect(self.actuate)
        self.dashboard.timestep_signal.connect(self.bold_active_step)
        self.dashboard.sequence_update_signal.connect(self.refresh)

    def activate(self, sequence):
        self.dashboard.post('hubs/%s/sequencer/activate'%self.hub, {'sequence': sequence})

    def delete(self):
        name = self.sequence_selector.currentText()
        if name == 'default':
            return
        self.dashboard.post('hubs/%s/sequencer/delete'%self.hub, {'name': name})
        self.sequence_selector.removeItem(self.sequence_selector.currentIndex())

    def store(self):
        name = self.store_edit.text()
        self.dashboard.post('hubs/%s/sequencer/store'%self.hub, {'name': name})
        self.sequence_selector.addItem(name)
        self.sequence_selector.setCurrentIndex(self.sequence_selector.count()-1)

    def add_table(self):
        self.ttls = self.dashboard.get('hubs/%s/sequencer/ttl'%self.hub)
        self.table = SequencerTable()
        timesteps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        self.table.set_channels(self.ttls)
        for step in timesteps:
            self.table.add_timestep(self.ttls, step)
        self.grid_layout.addWidget(self.table, 0, 0)
        self.table.adjustSize()
        self.widget.adjustSize()
        self.adjustSize()

    def add_labels(self):
        ''' Create TTL labels '''
        self.ttls = self.dashboard.get('hubs/%s/sequencer/ttl'%self.hub)
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
        self.adcs = self.dashboard.get('hubs/%s/sequencer/adc'%self.hub)
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
        self.dacs = self.dashboard.get('hubs/%s/sequencer/dac'%self.hub)
        label = BoldLabel('DAC')
        label.setBold(True)
        self.grid_layout.addWidget(label, row, 0)
        row += 1
        for dac in self.dacs:
            self.grid_layout.addWidget(QLabel(str(dac)), row, 0)
            row += 1
        #
        # ''' Create DDS labels '''
        # self.dds = self.dashboard.get('hubs/%s/sequencer/dds'%self.hub)
        # self.grid_layout.addWidget(QLabel('DDS'), row, 0)
        # row += 1
        # for dds in self.dds:
        #     self.grid_layout.addWidget(QLabel(str(dds)), row, 0)
        #     row += 1

    def refresh(self, sequence=None):
        # if sequence is None:
        sequence = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        self.redraw(sequence)

    def draw(self, sequence):
        self.order = []
        self.labels = {}
        self.step_edits = {}
        self.checkboxes = {}
        self.adc_checkboxes = {}
        self.dac_edits = {}
        col = 1
        row = 0
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
        for name in self.order:
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
        self.order.append(name)
        self.labels[name] = StepLabel(name, self)
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
                value = float(step['DAC'][int(dac)])
            elif str(dac) in step['DAC']:
                value = float(step['DAC'][str(dac)])
            else:
                value = 0.0
            edit = DACEdit(name, str(value), self.dashboard, self.hub, self)
            self.grid_layout.addWidget(edit, row, col)
            self.dac_edits[name][dac] = edit
            row += 1
        return row

    def remove_step(self, step):
        remove = [self.labels[step], self.step_edits[step]]
        for ttl in self.ttls:
            remove.append(self.checkboxes[step][ttl])
        for adc in self.adcs:
            remove.append(self.adc_checkboxes[step][adc])
        for dac in self.dacs:
            remove.append(self.dac_edits[step][dac])
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

    def insert_step(self, name, position = -1):
        step = {'name': name,
                'duration': 0,
                'TTL': [],
                'ADC': [],
                'DAC': {},
                'DDS': {}}
        if step in self.order:
            log.warn('Step already exists!')
            return
        steps = self.get_sequence()
        steps.insert(position, step)
        self.redraw(steps)

        self.dashboard.post('hubs/%s/sequencer/sequence'%self.hub, steps)

        ''' add knob '''
        self.dashboard.post('hubs/%s/devices/sequencer/exec'%self.hub, {'method': 'add_knob', 'args': (name,)})

    def move(self, step, n):
        ''' Moves the passed step (integer or string) n places to the left (negative n)
            or right (positive n). '''
        # steps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        steps = self.get_sequence()
        i = 0
        for s in self.order:
            if s == step:
                break
            i += 1
        if (i+n)<0 or (i+n) > len(steps)-1:
            return

        i_n = i
        for n0 in range(np.abs(n)):
            d_i = np.sign(n)
            adjacent_step = self.order[i_n+d_i]
            self.swap_timesteps(step, adjacent_step)
            steps.insert(i_n+d_i, steps.pop(i_n))
            self.order.insert(i_n+d_i, self.order.pop(i_n))
            i_n += d_i

        knob = self.dashboard.tree_widget.get_knob('hub', 'sequencer', step)
        knob.move(n)
        self.dashboard.post('hubs/%s/sequencer/sequence'%self.hub, steps)

    def swap(self, row1, col1, row2, col2):
        ''' Swaps two widgets '''
        widget1 = self.grid_layout.itemAtPosition(row1, col1).widget()
        widget2 = self.grid_layout.itemAtPosition(row2, col2).widget()
        self.grid_layout.removeWidget(widget1)
        self.grid_layout.removeWidget(widget2)
        self.grid_layout.addWidget(widget1, row2, col2)
        self.grid_layout.addWidget(widget2, row1, col1)

    def swap_columns(self, col1, col2):
        header_rows = [0, 1]        # headers
        ttl_rows = list(range(header_rows[-1]+2, header_rows[-1]+2+len(self.ttls)))
        header_rows.extend(ttl_rows)
        adc_rows = list(range(ttl_rows[-1]+2, ttl_rows[-1]+2+len(self.adcs)))
        header_rows.extend(adc_rows)
        dac_rows = list(range(adc_rows[-1]+2, adc_rows[-1]+2+len(self.dacs)))
        header_rows.extend(dac_rows)

        for row in header_rows:
            self.swap(row, col1, row, col2)
            time.sleep(1e-6)            # need a short pause here or Qt will crash

    def swap_timesteps(self, name1, name2):
        widget1 = self.labels[name1]
        index1 = self.grid_layout.indexOf(widget1)
        row1, col1, rowspan, colspan = self.grid_layout.getItemPosition(index1)
        widget2 = self.labels[name2]
        index2 = self.grid_layout.indexOf(widget2)
        row2, col2, rowspan, colspan = self.grid_layout.getItemPosition(index2)

        self.swap_columns(col1, col2)
