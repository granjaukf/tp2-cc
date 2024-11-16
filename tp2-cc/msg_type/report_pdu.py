import struct
from msg_type.base import PDUBase

class AlertPDU(PDUBase):
    def __init__(self, msg_type, seq_num, task_type, metric_value):
        super().__init__(msg_type, seq_num)
        self.task_type = task_type
        self.metric_value = metric_value

    def pack(self):
        base_packed = super().pack()
        task_type_packed = struct.pack('!B', self.task_type)
        metric_value_packed = struct.pack('!H', self.metric_value)
        return base_packed + task_type_packed + metric_value_packed

    @classmethod
    def unpack(cls, data):
        if len(data) < 5:
            raise ValueError("Dados insuficientes para desempacotar AlertPDU")
        
        base = PDUBase.unpack(data[:2])
        task_type = struct.unpack('!B', data[2:3])[0]
        metric_value = struct.unpack('!H', data[3:5])[0]

        return cls(base.msg_type, base.seq_num, task_type, metric_value)
