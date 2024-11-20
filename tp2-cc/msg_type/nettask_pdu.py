import struct
from msg_type.base import PDUBase
from tasks_payload.bandwidth_payload import BandwidthPayload
from tasks_payload.latency_payload import LatencyPayload
from tasks_payload.interface_payload import InterfacePayload
from tasks_payload.ram_payload import RAMPayload
from tasks_payload.cpu_payload import CPUPayload
from tasks_payload.jitter_payload import JitterPayload
from tasks_payload.packet_loss_payload import PacketLossPayload

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

        # Mapeamento de payloads com base no task_type
        payload_classes = {
            0: CPUPayload,
            1: RAMPayload,
            2: LatencyPayload,
            3: BandwidthPayload,
            4: JitterPayload,
            5: PacketLossPayload,
            6: InterfacePayload,
        }
        payload_class = payload_classes.get(task_type)
        if not payload_class:
            raise ValueError(f"Tipo de tarefa desconhecido: {task_type}")
        payload = payload_class.unpack(data[4:])
        return cls(base.msg_type, base.seq_num, freq, task_type, payload)

