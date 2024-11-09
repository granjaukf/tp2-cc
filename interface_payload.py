import struct

class InterfacePayload:
    def __init__(self, threshold_value, interface_name):
        self.threshold_value = threshold_value  
        self.interface_name = interface_name.ljust(10)[:10] 

    def pack(self):
        threshold_packed = struct.pack('!B', self.threshold_value & 0b1111111) 
        interface_packed = self.interface_name.encode()[:10] 
        return threshold_packed + interface_packed

    @classmethod
    def unpack(cls, data):
        threshold_value = struct.unpack('!B', data[:1])[0] & 0b1111111
        interface_name = data[1:11].decode().strip()
        return cls(threshold_value, interface_name)