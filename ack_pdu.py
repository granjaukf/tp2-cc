from base import PDUBase

class AckPDU(PDUBase):
    def __init__(self, msg_type, seq_num):
        super().__init__(msg_type, seq_num)
