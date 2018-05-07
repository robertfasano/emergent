def cleanRow(row):
    ''' Removes whitespace from row to enforce tab-delimitation only '''
    return formatRow(parseRow(row))

def formatRow(lst, newline = 'end', decs = [], lengths = []):
    ''' Converts a list of values into a tab-delimited string for file-output 
        If custom column output lengths are desired, pass a number into dec for each number of decimal places
        and into length for each total length'''
    row = ''
    for i in range(len(lst)):
        if len(decs) == 0:
            row += str(lst[i]) + '\t'
        else:
            row += ('{0:0.{prec}f}'.format(lst[i], prec=decs[i])).ljust(lengths[i], '0')+'\t'
    if newline == 'end':
        row = row[0:-1] + '\n'
    elif newline == 'start':
        row = '\n' + row[0:-1]
    elif newline == 'none':
        row = row[0:-1]
    return row

def parseRow(row):
    ''' Converts a row of tab-delimited values into a list '''
    lst = []
    for val in row.split('\t'):
        if val != '\n':
            lst.append(val.strip())    
    return lst

