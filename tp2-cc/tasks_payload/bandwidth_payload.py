import struct

class BandwidthPayload:
    def __init__(self, mode, server_ip, transport, duration, threshold_value):
        self.mode = mode  # "client" ou "server"
        self.server_ip = server_ip  # IP do servidor para cliente
        self.transport = transport  # "TCP" ou "UDP"
        self.duration = duration  # Duração do teste
        self.threshold_value = threshold_value  # Valor do threshold (1 byte)

    def pack(self):
        mode_encoded = 1 if self.mode == "client" else 0
        transport_encoded = 1 if self.transport == "TCP" else 0
        server_ip_bytes = self.server_ip.encode().ljust(15)  # 15 bytes para IP
        packet_data = struct.pack('!B15sBBB', mode_encoded, server_ip_bytes, transport_encoded, self.duration, self.threshold_value)
        return packet_data

    @classmethod
    def unpack(cls, data):
        mode_encoded, server_ip_bytes, transport_encoded, duration, threshold_value = struct.unpack('!B15sBBB', data[:20])
        mode = "client" if mode_encoded == 1 else "server"
        transport = "TCP" if transport_encoded == 1 else "UDP"
        server_ip = server_ip_bytes.decode().strip() 
        return cls(mode, server_ip, transport, duration, threshold_value)
