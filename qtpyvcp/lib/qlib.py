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






from qtpy.QtCore import QObject, Signal, Property, Slot


class Channel(QObject):

    valueChanged = Signal(object)

    def __init__(self, fget=None, fset=None, fquery=None, doc=None, value=None):
        super(Channel, self).__init__()

        self.getValue = fget or self._getValue
        self.setValue = fset or self._setValue
        self.handleQuery = fquery or self._handleQuery

        self._value = value

        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def _getValue(self):
        print 'Getting value'
        return self._value

    def _setValue(self, value):
        print 'Setting value'
        self._value = value
        self.valueChanged.emit(value)

    def _handleQuery(self, item):
        raise NotImplemented

    def connect(self, *args, **kwargs):
        print "connect", args
        self.valueChanged.connect(*args, **kwargs)

    def __str__(self):
        return "hello"

class Test(object):
    def __init__(self):
        pass

    tool = Channel(value=[1, 2, 3, 4], doc='Current Tool Data')

    def toolQuery(item):
        t.tool._value[item]

    tool.handleQuery = toolQuery


# t = Test()
# print t.tool
#
# def valueChanged(value):
#     print 'changed', value
#
#
# print 'val', t.tool.getValue()
# # print t.tool.test
#
# t.tool.connect(valueChanged)
#
# print 'query', t.tool.handleQuery(2)
#
# t.tool.setValue(45)
#
# print str(t.tool)
#
# print t.tool.__doc__





class ChannelTwo(QObject):

    valueChanged = Signal(object)

    def __init__(self, fget=None, fset=None, fquery=None, doc=None, value=None):
        super(ChannelTwo, self).__init__()


    # def getter(self, key):
    #     print key
    #
    #     def decorator(func):
    #         def inner(*args, **kwargs):
    #
    #             return func(*args, **kwargs)
    #
    #         return inner
    #
    #     setattr(self, key, decorator)
    #     return
    #
    #
    # def setter(self, key):
    #
    #     print key
    #
    #     def decorator(func):
    #         def inner(*args, **kwargs):
    #
    #             return func(*args, **kwargs)
    #
    #         return inner
    #
    #     setattr(self, key, decorator)
    #     return self

    def getter(self, key):
        print key
        def decorator(func):
            print 'func:', func

            def inner(*args, **kwargs):
                func(*args, **kwargs)

            return inner

        return decorator
        # return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, func):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)



tool = ChannelTwo(value={}, doc='current tool data')

tool_dict = {'diameter': 0.125}

print tool
@tool.getter('diameter')
def tool(self):
    return tool_dict['diameter']

print tool

print tool('hello')

# @tool.setter('diameter')
# def tool(self, value):
#     tool_dict['diameter'] = value






class PProperty(object):
    """Emulate PyProperty_Type() in Objects/descrobject.c"""

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __getattr__(self, item):
        print "getattr"
        return

    def __get__(self, obj, objtype=None):
        print 'Getting', self.fget
        if obj is None:
            print 'obj is none'
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        print 'Setting'
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def connect(self, slot):
        print "connecting", slot

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)









# class Test(QObject):
#
#     valueChanged = Signal(int)
#
#     def __init__(self):
#         super(Test, self).__init__()
#
#         self._value = 1234
#
#     # @Property(bool, notify=valueChanged)
#     def getValue(self):
#         print 'getting val'
#         return self._value
#
#     # @value.setter
#     def setValue(self, value):
#         self._value = value
#
#     value = Property(int, fget=getValue, fset=setValue, notify=valueChanged)
#
# t = Test()
#
# # @Slot(int)
# def log_change(val=None):
#     print '#########'
#     print val
#
# t.valueChanged.connect(log_change)
#
# print t.value
# t.value = 4321
# print t.value
