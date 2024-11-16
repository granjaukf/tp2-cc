import struct
from msg_type.base import PDUBase
from tasks_payload.throughput_payload import ThroughputPayload
from tasks_payload.latency_payload import LatencyPayload
from tasks_payload.interface_payload import InterfacePayload
from tasks_payload.ram_payload import RAMPayload
from tasks_payload.cpu_payload import CPUPayload

class NetTaskPDU(PDUBase):
    def __init__(self, msg_type, seq_num, freq, task_type, payload):
        super().__init__(msg_type, seq_num)
        self.freq = freq
        self.task_type = task_type
        self.payload = payload

    def pack(self):
        base_packed = super().pack()
        freq_task = struct.pack('!BB', self.freq, self.task_type)
        payload_packed = self.payload.pack()
        return base_packed + freq_task + payload_packed

    @classmethod
    def unpack(cls, data):
        if len(data) < 4:
            raise ValueError("Dados insuficientes para desempacotar NetTaskPDU")
        
        base = PDUBase.unpack(data[:2])
        freq, task_type = struct.unpack('!BB', data[2:4])

        # Escolhe o payload com base no task_type
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
            raise ValueError(f"Tipo de tarefa desconhecido: {task_type}")

        return cls(base.msg_type, base.seq_num, freq, task_type, payload)
