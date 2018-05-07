import serial

class Serial():
    def __init__(self, port = 'COM1', baudrate = 19200, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1, encoding = 'ascii'):
        self.port, self.baudrate, self.parity, self.stopbits, self.bytesize, self.timeout, self.encoding = port, baudrate, parity, stopbits, bytesize, timeout, encoding
        self.connect()
        
    def connect(self):
        self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout = self.timeout
            )
        
        if self.ser.isOpen():
            self.ser.close()
#        if self.ser.isOpen() != 1:
        self.ser.open()
            
    def command(self, cmd):
        cmd += '\r'
        self.ser.write(cmd.encode(self.encoding))
        reply = self.ser.readline()
        
        return reply.decode()
    
    def close(self):
        self.ser.close()   