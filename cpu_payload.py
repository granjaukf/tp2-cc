import struct

class CPUPayload:
    def __init__(self, threshold_value):
        self.threshold_value = threshold_value
    
    def pack(self):
        return struct.pack('!B', self.threshold_value & 0b1111111)  # 7 bits

    @classmethod
    def unpack(cls, data):
        threshold_value = struct.unpack('!B', data[:1])[0] & 0b1111111
        return cls(threshold_value)