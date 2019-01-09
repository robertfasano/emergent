from influxdb import InfluxDBClient

class TICKClient():
    def __init__(self, addr, username, password, database):
        self.client = InfluxDBClient(addr, 8086, username, password, database)
        self.database = database

    def read(self, limit = None, measurement='state'):
        query = 'select * from %s."autogen".%s'%(self.database,measurement)
        if limit is not None:
            query += ' LIMIT %i'%limit
        return self.client.query(query)

    def write(self, d, measurement = 'state'):
        payload = [{'measurement': measurement, 'fields': d}]
        self.client.write_points(payload)

    def write_network_state(self, state):
        for hub in state:
            data = {}
            for dev in state[hub]:
                for input in state[hub][dev]:
                    full_name = dev+': '+input
                    data[full_name] = state[hub][dev][input]
            self.write(data, measurement = hub)



if __name__ == '__main__':
    client = TICKClient('3.17.63.193', 'dweet', 'dweet', 'dweet')
