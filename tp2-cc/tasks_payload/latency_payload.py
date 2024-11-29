import struct

class LatencyPayload:
    def __init__(self, threshold_value, destination, count, frequency):
        self.threshold_value = threshold_value  # Limite de valor (7 bits)
        self.destination = destination  # Destino para o ping
        self.count = count  # Contagem de pacotes
        self.frequency = str(frequency).ljust(4)[:4]  # Frequência como string, máximo 5 caracteres
    
    def pack(self):
        # Codifica `threshold_value` com 7 bits e `destination` com 15 bytes
        threshold_packed = self.threshold_value & 0b1111111
        destination_bytes = self.destination.encode().ljust(15)  # 15 bytes para IP ou destino
        frequency_bytes = self.frequency.encode().ljust(4)  # Frequência em string, 4 bytes
        return struct.pack('!B15sB5s', threshold_packed, destination_bytes, self.count, frequency_bytes)

    @classmethod
    def unpack(cls, data):
        # Desempacota a estrutura com `frequency` como string
        threshold_value, destination_bytes, count, frequency_bytes = struct.unpack('!B15sB5s', data[:22])
        threshold_value &= 0b1111111  # Extrai apenas os 7 bits mais baixos para o threshold
        destination = destination_bytes.decode().strip()
        frequency = frequency_bytes.decode().strip()
        return cls(threshold_value, destination, count, frequency)
