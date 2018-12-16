from qtpy import QtCore

class QtPyVCPSignal(QtCore.QObject):

    def __init__(self, *args, **kwargs):
        class _SignalQObject(QtCore.QObject):
            signal = QtCore.Signal(*args, **kwargs)

        self.object_cls = _SignalQObject()
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.emit(value)

    def emit(self, value):
        self._value = value
        self.object_cls.signal.emit(value)

    def __getattr__(self, item):
        return getattr(self.object_cls.signal, item)
