from emergent import Q_
import numpy as np
from PyQt5.QtWidgets import QLineEdit

class UnitEdit(QLineEdit):
    def __init__(self, text, base_unit = 's'):
        super().__init__(text)
        self.base_unit = base_unit
        self.convert_units()
        self.returnPressed.connect(self.convert_units)

    def convert_units(self):
        if self.text() == '':
            return
        duration = Q_(self.text())
        if str(duration.units) == 'dimensionless':
            duration = Q_('{} {}'.format(duration.magnitude, self.base_unit))    # assume base unit if none is passed
        cleaned_value = duration.to_compact()                   # auto-convert units for compact view
        cleaned_value = np.round(cleaned_value, 9)              # round to 9 digits to remove numerical rounding errors in Python
        self._setText('{:~}'.format(cleaned_value))
        duration.ito_base_units()
        self.magnitude = duration.magnitude     # store magnitude in base unit

    def setText(self, text):
        self._setText(text)
        self.convert_units()

    def _setText(self, text):
        QLineEdit.setText(self, text)
