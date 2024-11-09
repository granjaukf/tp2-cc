import struct

class LatencyPayload:
    def __init__(self, threshold_value, destination, count, frequency):
        self.threshold_value = threshold_value  # Limite de valor (7 bits)
        self.destination = destination  # Destino para o ping
        self.count = count  # Contagem de pacotes
        self.frequency = frequency  # Frequência do teste
    
    def pack(self):
        threshold_packed = self.threshold_value & 0b1111111  # 7 bits para threshold
        destination_bytes = self.destination.encode().ljust(15)  # 15 bytes para IP ou nome do destino
        return struct.pack('!B15sBB', threshold_packed, destination_bytes, self.count, self.frequency)

    @classmethod
    def unpack(cls, data):
        threshold_value, destination_bytes, count, frequency = struct.unpack('!B15sBB', data[:18])
        threshold_value &= 0b1111111  # Extrai apenas os 7 bits mais baixos para o threshold
        destination = destination_bytes.decode().strip()
        return cls(threshold_value, destination, count, frequency)
