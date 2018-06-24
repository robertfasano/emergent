import serial

PARITY_NONE = serial.PARITY_NONE 
STOPBITS_ONE = serial.STOPBITS_ONE
EIGHTBITS = serial.EIGHTBITS

class Serial():
    def __init__(self, port = 'COM1', baudrate = 19200, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1, encoding = 'ascii'):
        self.port, self.baudrate, self.parity, self.stopbits, self.bytesize, self.timeout, self.encoding = port, baudrate, parity, stopbits, bytesize, timeout, encoding
        self._connected = 0
        self.connect()
        
    def connect(self):
        try:
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
            self._connected = 1
        except serial.serialutil.SerialException:
            print('Could not open port %s'%self.port)
            
    def command(self, cmd, output = False, reply = True, suffix = '\r'):
        cmd += suffix
        self.ser.write(cmd.encode(self.encoding))
        if reply:
            reply = self.ser.readline()
            if output:
                print('Sent: %s'%cmd.encode(self.encoding))
                print('Received: %s'%reply.decode())
    
            return reply.decode()
    
    def close(self):
        self.ser.close()   