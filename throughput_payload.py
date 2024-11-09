import struct

class ThroughputPayload:
    def __init__(self, threshold_value, mode, server_ip, transport, duration):
        self.threshold_value = threshold_value  # Limite de valor (7 bits)
        self.mode = mode  # "client" ou "server"
        self.server_ip = server_ip  # IP do servidor para cliente
        self.transport = transport  # "TCP" ou "UDP"
        self.duration = duration  # Duração do teste
   
    def pack(self):
        threshold_packed = self.threshold_value & 0b1111111  # 7 bits para threshold
        mode_encoded = 1 if self.mode == "client" else 0
        transport_encoded = 1 if self.transport == "TCP" else 0
        server_ip_bytes = self.server_ip.encode().ljust(15)  # 15 bytes para IP
        packet_data = struct.pack('!BBB15sB', threshold_packed, mode_encoded, transport_encoded, server_ip_bytes, self.duration)
        return packet_data
    
    @classmethod
    def unpack(cls, data):
        threshold_value, mode_encoded, transport_encoded, server_ip_bytes, duration = struct.unpack('!BBB15sB', data[:19])
        threshold_value &= 0b1111111  # Extrai apenas os 7 bits mais baixos para o threshold
        mode = "client" if mode_encoded == 1 else "server"
        transport = "TCP" if transport_encoded == 1 else "UDP"
        server_ip = server_ip_bytes.decode().strip()
        return cls(threshold_value, mode, server_ip, transport, duration)