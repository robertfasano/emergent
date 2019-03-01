import pint

class Units():
    def __init__(self):
        self.units = pint.UnitRegistry()
        self.unit_list = ['V', 'Hz']

    def parse(self, string):
        ''' Converts a dimensional string into a scaled float'''

        ''' e.g. mV multiples by 1e-3, while V does not scale '''

        value = float(string.split(' ')[0])
        unit = string.split(' ')[1]
        base_unit = self.get_base_unit(unit)

        qty = value*getattr(self.units, unit)

        return qty.m_as(base_unit)

    def get_base_unit(self, unit):
        ''' check which base unit we're using '''
        for u in self.unit_list:
            if u in unit:
                return u

    def get_scaling(self, unit):
        ''' Gets the scaling factor between a passed unit and its base unit. 
            For example, calling this function on 'mV' returns 1e-3. '''
        base_unit = self.get_base_unit(unit)
        return (1*getattr(self.units, unit)).m_as(base_unit)

if __name__ == '__main__':
    u = Units()
    qty = u.get_scaling('mV')
