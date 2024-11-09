import struct

class PDUBase:
    def __init__(self,msg_type, seq_num):
        self.msg_type = msg_type
        self.seq_num = seq_num
    
    def pack(self):
        # primeiro byte: 3 bits para o msg_type, seguido de 5 bits de zeros
        first_byte = (self.msg_type << 5) & 0b11100000
        
        #segundo byte: seq_num ocupa todos os 8 bits
        second_byte = self.seq_num
        
        # retorna a parte comum dos dados empacotados
        return struct.pack('!BB',first_byte,second_byte)
    @classmethod
    def unpack(cls,data):
        first_byte, seconde_byte = struct.unpack('!BB',data[:2])
        
        msg_type = (first_byte >> 5) & 0b111
        
        seq_num = seconde_byte
        
        return cls(msg_type,seq_num)
        
        