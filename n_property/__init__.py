# encoding: utf-8
import weakref
import sys
import types
import logging
from functools import wraps


def get_frame_id(depth=1):
    frame = sys._getframe(depth)
    r = "%s:%s:%s" % (frame.f_code.co_filename, frame.f_lineno, frame.f_code.co_name)  # noqa pylint: disable=C,W
    return r


class NError(Exception):
    pass


class n_property(object):
    '''
    解决成本较高的 property 调用的n+1问题
    开发者定义property时即定义取得批量结果的方法，使用时正常使用。
    在同一批对象的该property被第二次使用时，自动批量预获取同一批对象剩余的property
    注意：定义n_property时必须保证结果数量与传入的selfs数量一致，否则report error 并fallback成None值
    '''
    sessions = {}
    counts = {}

    def __init__(self, fallback=None):
        self.fallback = None
        self.func = None
        self.__name__ = ''
        self.is_classmethod = False

        if isinstance(fallback, types.FunctionType):
            self._init_func(fallback)
        else:
            self.fallback = fallback

    def _init_func(self, func):
        self.func = func
        if not self.is_classmethod:
            self.__name__ = func.__name__

    def __call__(self, func):
        if isinstance(func, classmethod):
            raise NError('Please use @[property_name].n_getter !!!')

        self._init_func(func)
        return self

    def n_getter(self, func):
        self.is_classmethod = True
        if isinstance(func, classmethod):
            self._init_func(func.__func__)
            return func
        return classmethod(func)

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        frame_id = obj._nc_frame_id
        session_key = (objtype, frame_id)
        count_key = (frame_id, self.__name__)

        session = self.sessions.get(session_key)
        count = self.counts.get(count_key, 0)
        self.counts[count_key] = count + 1

        if not session:
            insts = [obj]
        else:
            _session = []
            insts = [r() for r in session]
            _session = [r for r, i in zip(session, insts) if i is not None]
            insts = [i for i in (insts + [obj]) if i and self.__name__ not in i.__dict__]
            self.sessions[session_key] = _session

        if count < 1:
            insts = [obj]

        if self.is_classmethod:
            res = self.func(obj.__class__, insts)
        else:
            res = self.func(insts)

        if len(res) != len(insts):
            self.report(msg='n_property length mismatch: %s' % self.__name__, level=logging.ERROR)
            res = [self.fallback] * len(insts)  # 数量不一致直接提供默认值

        if len(insts) > 1:
            self.counts.pop(count_key, None)

        for inst, r in zip(insts, res):
            inst.__dict__[self.__name__] = r  # 写入对象，替换property
        return obj.__dict__[self.__name__]
    
    def __set_name__(self, owner, name):
        n_class(owner)

    report = lambda *args, **kwargs: None

    @classmethod
    def set_report(cls, func):
        cls.report = func


def n_class(cls):
    for k, v in cls.__dict__.items():
        if isinstance(v, n_property):
            v.__name__ = k

    if hasattr(cls, '__nc_flag__'):
        return cls

    old_new = cls.__new__

    @classmethod
    @wraps(old_new)
    def new(_cls, *args, **kwargs):

        if old_new is object.__new__:
            inst = old_new(_cls)
        else:
            inst = old_new(_cls, *args, **kwargs)

        frame_id = get_frame_id(2)
        inst._nc_frame_id = frame_id
        ref = weakref.ref(inst)
        session_key = (_cls, frame_id)
        if n_property.sessions.get(session_key) is None:
            n_property.sessions[session_key] = []
        n_property.sessions[session_key].append(ref)

        return inst

    cls.__new__ = new
    cls.__nc_flag__ = True

    return cls
