def cleanRow(row):
    ''' Removes whitespace from row to enforce tab-delimitation only '''
    return formatRow(parseRow(row))

def formatRow(lst, newline = 'end'):
    ''' Converts a list of values into a tab-delimited string for file-output '''
    row = ''
    for val in lst:
        row += str(val) + '\t'
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