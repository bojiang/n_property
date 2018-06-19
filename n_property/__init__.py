# encoding: utf-8
import inspect
import weakref
import sys
import types
import logging
from functools import partial, wraps

from .utils import HashableList, HashableDict


_missing = object()


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


class NMethod(object):
    """解决成本较高的 method 调用的 n+1 问题

    开发者定义 method 时即定义取得批量结果的方法，使用时正常使用。
    在同一批对象的该 method 被第二次使用时，自动批量预获取同一批对象剩余的 method 的返回值
    注意：
    - 定义 n_method 的 implement 时必须保证结果数量与传入的 insts 数量一致，否则 report error 并返回 fallback 值
    - 请使用装饰器 @n_method
    """
    sessions = {}
    counts = {}

    def __init__(self, fallback=None, implement=''):
        self.fallback = fallback
        self.implement = implement

        if not isinstance(self.fallback, types.FunctionType):
            raise NError('Please use @n_method deecorator !!!')
        if isinstance(self.fallback, classmethod):
            raise NError('Please use instance method in @n_method !!!')
        if not isinstance(self.implement, str) or not self.implement:
            raise NError('Please use str as implement !!!')

    def __get__(self, obj, objtype=None):
        if obj is None:
            return getattr(objtype, self.implement)
        return partial(self, obj)

    def _get_obj_cache(self, obj, key):
        try:
            cache = obj.__n_cache
        except AttributeError:
            cache = obj.__n_cache = {}
        try:
            return cache[key]
        except KeyError:
            return _missing

    def _set_obj_cache(self, obj, key, val):
        try:
            cache = obj.__n_cache
        except AttributeError:
            cache = obj.__n_cache = {}
        cache[key] = val

    def __call__(self, *args, **kwargs):
        obj = args[0]
        implement = getattr(obj.__class__, self.implement)
        if not (
            inspect.ismethod(implement) and
            implement.__self__ is obj.__class__
        ):
            raise NError('Please use classmethod for implement !!!')

        key = (self.fallback, HashableList(args[1:]), HashableDict(kwargs))
        val = self._get_obj_cache(obj, key)
        if val is not _missing:
            return val

        frame_id = obj._nc_frame_id
        session_key = (type(obj), frame_id)
        count_key = (frame_id, self.fallback.__name__)

        session = self.sessions.get(session_key)
        count = self.counts.get(count_key, 0)
        self.counts[count_key] = count + 1

        if not session:
            insts = [obj]
        else:
            _session = []
            insts = [r() for r in session]
            _session = [r for r, i in zip(session, insts) if i is not None]
            insts = [i for i in insts if i and self._get_obj_cache(i, key) is _missing]
            self.sessions[session_key] = _session

        if count < 1:
            insts = [obj]

        res = implement(insts, *args[1:], **kwargs)
        fallback_res = self.fallback(*args, **kwargs)
        if len(res) != len(insts):
            self.report(msg='n_method length mismatch: %s' % fallback_res, level=logging.ERROR)
            res = [fallback_res] * len(insts)  # 数量不一致直接提供默认值

        if len(insts) > 1:
            self.counts.pop(count_key, None)

        for inst, r in zip(insts, res):
            self._set_obj_cache(inst, key, r)
        val = self._get_obj_cache(obj, key)
        return val if val is not _missing else fallback_res

    def report(self, msg='', level=logging.INFO, *args, **kwargs):
        logging.log(level, msg)


def n_method(implement):
    return partial(NMethod, implement=implement)


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
        if NMethod.sessions.get(session_key) is None:
            NMethod.sessions[session_key] = []
        NMethod.sessions[session_key].append(ref)

        return inst

    cls.__new__ = new
    cls.__nc_flag__ = True

    return cls
