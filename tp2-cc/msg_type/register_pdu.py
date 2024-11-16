import struct
from msg_type.base import PDUBase

class RegisterPDU(PDUBase):
    def __init__(self, msg_type, seq_num, agent_id):
        super().__init__(msg_type, seq_num)
        self.agent_id = agent_id.ljust(20)[:20]  # Preenche ou corta para 20 bytes

    def pack(self):
        base_packed = super().pack()
        agent_id_packed = self.agent_id.encode()[:20]
        return base_packed + agent_id_packed

    @classmethod
    def unpack(cls, data):

        if len(data) < 22:
            raise ValueError("Dados insuficientes para desempacotar RegisterPDU")
        
        base = PDUBase.unpack(data[:2])
        agent_id = data[2:22].decode().strip()

        return cls(base.msg_type, base.seq_num, agent_id)
