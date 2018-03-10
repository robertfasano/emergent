import numpy as np

def convertUnits(edit, precision = 3):
    ''' Allows unit comprehension by detecting SI prefixes and converting to an absolute value in base SI units, e.g. '10 mV' -> 0.01.
        TODO: allow context-based reverse comprehension: given a float and a base unit (e.g. V) a string will be returned, e.g. 0.01 -> '10 mV'
        Arguments: 
            edit (str): text stored in a QLineEdit() object on the panel, which includes a value and a unit
        Returns:
            val (float): a value in base SI units
    '''   
    if type(edit) == str:
    
        val = float(edit.split(' ')[0])
        unit = edit.split(' ')[1]
        prefix = unit[0]
        if len(unit) > 1:
            prefixDict = {'m':1e-3, 'u':1e-6, 'n':1e-9}
            return val*prefixDict[prefix]
        else:
            return val
    elif type(edit) == float:
        edit = np.round(edit, precision)
        if edit == 0:
            return str(0)
        # check number of zeros
        stringEdit = str(edit)
        leading = stringEdit[0]
        prefix = ''
        if leading == '0':
            zeroCount = 1
        elif leading != '-':
            return str(edit) + ' V'
        elif leading == '-':
            stringEdit = stringEdit[1::]
            prefix = '-'
            leading = stringEdit[0]
            if leading == '0':
                zeroCount = 1
            else:
                return prefix + str(edit) + ' V'
        readingZeros = 1
        i=0
        while readingZeros:
            if stringEdit[2+i] == '0':
                zeroCount += 1
                i += 1
            else:
                readingZeros = 0
        # valueEdit will always have 3 sigfigs but will omit trailing zeros, so we should add these back
        # The target length is zeroCount + 1 + 3; add however many zeros we need to 
        numZerosToAdd = zeroCount + 1 + 3 - len(stringEdit)
        stringEdit += '0'*numZerosToAdd
        if zeroCount == 0:
            return prefix + stringEdit
        elif zeroCount == 1:
            return prefix + stringEdit[2::] + ' mV'
        elif zeroCount == 2:
            return prefix + stringEdit[3:5] + '.' + stringEdit[5] + ' mV'
        elif zeroCount == 3:
            return prefix + stringEdit[4:5] + '.' + stringEdit[5:6] + ' mV'
        elif zeroCount == 4:
            return prefix + stringEdit[5::] + ' uV'
        elif zeroCount == 5:
            return prefix + stringEdit[6:8] + '.' + stringEdit[8] + 'uV'

        ''' general form: 
        if zeroCount in [1,2]:
            return prefix + stringEdit[zeroCount+1::] + 'mV'
        elif zeroCount in [2,3]:
            return prefix + stringEdit[zeroCount+1:5] + '.' + stringEdit[5:zeroCount+3] + 'mV'
        elif zeroCount in [4,5]:
            ?
        '''