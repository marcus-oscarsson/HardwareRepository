from HardwareRepository.HardwareObjects.abstract.AbstractActuator import (
    AbstractActuator,
)

class TransmissionMockup(AbstractActuator):
    def __init__(self, name):
        super(TransmissionMockup, self).__init__(name)
        self.labels = []
        self.bits = []
        self.attno = 0
        self.value = 100

    def init(self):
        pass

    def get_value(self):
        return self.value

    def _set_value(self, value):
        self.value = value
        self.emit("valueChanged", self.value)

    def connected(self):
        self.setIsReady(True)

    def disconnected(self):
        self.setIsReady(False)

    def isReady(self):
        return True
