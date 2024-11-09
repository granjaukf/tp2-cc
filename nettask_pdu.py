import struct
from base import PDUBase
from throughput_payload import ThroughputPayload
from latency_payload import LatencyPayload
from interface_payload import InterfacePayload
from ram_payload import RAMPayload
from cpu_payload import CPUPayload


class NetTaskPDU(PDUBase):
    def __init__(self, msg_type, seq_num, freq, task_type, payload):
        super().__init__(msg_type, seq_num)
        self.freq = freq
        self.task_type = task_type
        self.payload = payload
    
    def pack(self):
        # Empacota a parte comum (msg_type e seq_num)
        base_packed = super().pack()
        
        # Empacota freq e task_type
        freq_task = struct.pack('!BB', self.freq, self.task_type)
        
        # Empacota o payload específico da tarefa
        payload_packed = self.payload.pack()
        
        # Junta todos os pedaços empacotados
        return base_packed + freq_task + payload_packed
    
    @classmethod
    def unpack(cls, data):
        # Desempacota a parte comum
        base = PDUBase.unpack(data[:2])
        
        # Desempacota freq e task_type
        freq, task_type = struct.unpack('!BB', data[2:4])
        
        # Determina a classe de payload com base no task_type
        if task_type == 0:  # CPU
            payload = CPUPayload.unpack(data[4:])
        elif task_type == 1:  # RAM
            payload = RAMPayload.unpack(data[4:])
        elif task_type == 2:  # Latency
            payload = LatencyPayload.unpack(data[4:])
        elif task_type == 3:  # Throughput
            payload = ThroughputPayload.unpack(data[4:])
        elif task_type == 4:  # Interface
            payload = InterfacePayload.unpack(data[4:])
        else:
            raise ValueError("Unknown task type")
        
        # Retorna a instância de NetTaskPDU com o payload adequado
        return cls(base.msg_type, base.seq_num, freq, task_type, payload)

