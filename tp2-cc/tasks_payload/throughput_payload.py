import struct

class ThroughputPayload:
    def __init__(self, jitter_threshold, packet_loss_threshold, mode, server_ip, transport, duration):
        self.jitter_threshold = jitter_threshold  # Limite para jitter (7 bits)
        self.packet_loss_threshold = packet_loss_threshold  # Limite para perda de pacotes (7 bits)
        self.mode = mode  # "client" ou "server"
        self.server_ip = server_ip  # IP do servidor para cliente
        self.transport = transport  # "TCP" ou "UDP"
        self.duration = duration  # Duração do teste

    def pack(self):
        jitter_packed = self.jitter_threshold & 0b1111111  # 7 bits para jitter
        packet_loss_packed = self.packet_loss_threshold & 0b1111111  # 7 bits para perda de pacotes
        mode_encoded = 1 if self.mode == "client" else 0
        transport_encoded = 1 if self.transport == "TCP" else 0
        server_ip_bytes = self.server_ip.encode().ljust(15)  # 15 bytes para IP
        # Adiciona jitter e packet_loss no início
        packet_data = struct.pack('!BB15sBBB', jitter_packed, packet_loss_packed, server_ip_bytes, mode_encoded, transport_encoded, self.duration)
        return packet_data

    @classmethod
    def unpack(cls, data):
        jitter_threshold, packet_loss_threshold, server_ip_bytes, mode_encoded, transport_encoded, duration = struct.unpack('!BB15sBBB', data[:20])
        jitter_threshold &= 0b1111111  # Extrai os 7 bits mais baixos para jitter
        packet_loss_threshold &= 0b1111111  # Extrai os 7 bits mais baixos para perda de pacotes
        mode = "client" if mode_encoded == 1 else "server"
        transport = "TCP" if transport_encoded == 1 else "UDP"
        server_ip = server_ip_bytes.decode().strip()
        return cls(jitter_threshold, packet_loss_threshold, mode, server_ip, transport, duration)
