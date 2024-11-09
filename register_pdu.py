from base import PDUBase

class RegisterPDU(PDUBase):
    def __init__(self, msg_type, seq_num, agent_id):
        super().__init__(msg_type, seq_num)
        # Ajusta `agent_id` para ter exatamente 20 bytes
        self.agent_id = agent_id.ljust(20)[:20]  # Preenche ou corta para garantir 20 bytes

    def pack(self):
        # Empacota a parte base (msg_type e seq_num)
        base_packed = super().pack()
        
        # Converte `agent_id` para bytes e garante que ele ocupe exatamente 20 bytes
        agent_id_packed = self.agent_id.encode()[:20]  # Converte string para 20 bytes
        
        # Retorna a combinação do pacote base com o `agent_id`
        return base_packed + agent_id_packed

    @classmethod
    def unpack(cls, data):
        # Desempacota a parte comum (msg_type e seq_num)
        base = PDUBase.unpack(data[:2])
        
        # Desempacota `agent_id` de 20 bytes e decodifica como string
        agent_id = data[2:22].decode().strip()  # Remove espaços adicionais, se houver
        
        return cls(base.msg_type, base.seq_num, agent_id)
