import struct
from msg_type.base import PDUBase

class MetricPDU(PDUBase):
    def __init__(self, msg_type, seq_num, task_type, metric_value):
        super().__init__(msg_type, seq_num)
        self.task_type = task_type
        self.metric_value = metric_value

    def pack(self):
        """Empacota a PDU incluindo o valor da métrica como float"""
        base_packed = super().pack()
        task_type_packed = struct.pack('!B', self.task_type)

        # Converte metric_value para string e empacota o tamanho seguido do valor
        metric_value_str = f"{self.metric_value:.8f}".encode('utf-8')
        metric_value_length = len(metric_value_str)
        metric_value_packed = struct.pack(f"!H{metric_value_length}s", metric_value_length, metric_value_str)

        return base_packed + task_type_packed + metric_value_packed

    @classmethod
    def unpack(cls, data):
        """Desempacota a PDU incluindo o valor da métrica como float"""
        if len(data) < 5:
            raise ValueError("Dados insuficientes para desempacotar MetricPDU")

        # Desempacota os campos base e task_type
        base = PDUBase.unpack(data[:2])
        task_type = struct.unpack('!B', data[2:3])[0]

        # Desempacota o comprimento do metric_value e o valor
        metric_value_length = struct.unpack('!H', data[3:5])[0]
        metric_value_str = struct.unpack(f"!{metric_value_length}s", data[5:5 + metric_value_length])[0]
        metric_value = float(metric_value_str.decode('utf-8'))

        return cls(base.msg_type, base.seq_num, task_type, metric_value)
