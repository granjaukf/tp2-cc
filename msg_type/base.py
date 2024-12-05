import struct

class PDUBase:
    HEADER_FORMAT = '!BB'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, msg_type, seq_num):
        if not (0 <= msg_type <= 7):
            raise ValueError(f"msg_type inválido: {msg_type}. Deve estar entre 0 e 7.")
        if not (0 <= seq_num <= 255):
            raise ValueError(f"seq_num inválido: {seq_num}. Deve estar entre 0 e 255.")
        self.msg_type = msg_type
        self.seq_num = seq_num

    def pack(self):
        first_byte = (self.msg_type << 5) & 0b11100000
        second_byte = self.seq_num
        return struct.pack(self.HEADER_FORMAT, first_byte, second_byte)

    @classmethod
    def unpack(cls, data):
        if len(data) < cls.HEADER_SIZE:
            raise ValueError("Dados insuficientes para desempacotar PDUBase.")
        first_byte, second_byte = struct.unpack(cls.HEADER_FORMAT, data[:cls.HEADER_SIZE])
        msg_type = (first_byte >> 5) & 0b111
        seq_num = second_byte
        return cls(msg_type, seq_num)

