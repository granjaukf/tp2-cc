from msg_type.base import PDUBase

class RegisterPDU(PDUBase):
    def __init__(self, msg_type, seq_num, agent_id):
        super().__init__(msg_type, seq_num)
        self.agent_id = agent_id.ljust(5)[:5]  # Ajusta para exatamente 5 bytes

    def pack(self):
        base_packed = super().pack()
        agent_id_packed = self.agent_id.encode()[:5]  # Garante 5 bytes para o agente
        return base_packed + agent_id_packed

    @classmethod
    def unpack(cls, data):
        if len(data) < 7:  # Base (2 bytes) + agent_id (5 bytes)
            raise ValueError("Dados insuficientes para desempacotar RegisterPDU")
        base = PDUBase.unpack(data[:2])
        agent_id = data[2:7].decode().strip()  # Lê 5 bytes para o agente
        return cls(base.msg_type, base.seq_num, agent_id)
