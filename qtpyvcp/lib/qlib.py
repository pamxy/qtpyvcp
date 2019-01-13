from qtpy.QtCore import QObject, Signal


class Channel(QObject):

    _signal = Signal(object)

    def __init__(self, fget=None, fset=None, doc=None, data=None):
        super(Channel, self).__init__()

        self.getData = fget or self._getData
        self.setData = fset or self._setData

        self._data = data

        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    @property
    def value(self):
        return self._data

    def _getData(self):
        print 'Getting value'
        return self._data

    def _setData(self, data):
        print 'Setting value'
        self._data = data
        self._signal.emit(data)

    def notify(self, *args, **kwargs):
        print "connect", args
        self._signal.connect(*args, **kwargs)

    def __str__(self):
        return str(self._data)

    def __getitem__(self, key):
        return self._data.__getitem__(key)

class Test(object):

    tool = Channel(data={'test': 2}, doc='Current Tool Data')

    def __init__(self):
        pass

if __name__ == "__main__":
    t = Test()

    print t.tool
    print t.tool.getData()
    print t.tool['test']

    def valueChanged(value):
        print 'changed', value

    t.tool.notify(valueChanged)

    t.tool.setData(45)

    print str(t.tool)

    print t.tool.__doc__
