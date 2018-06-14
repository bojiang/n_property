# -*- coding: utf-8 -*-
import unittest
from n_property import n_class, n_method, accept_argument, NError


class NClassTestCase(unittest.TestCase):

    def test_n_method(self):
        @n_class
        class NC(object):
            def __init__(self, a):
                self.a = a

            def __repr__(self):
                return 'NC(a=%s)' % self.a

            p = n_method(accept_argument=accept_argument(int))

            @p.n_call
            @classmethod
            def get_ps(cls, insts, incr):
                ids = [self.a for self in insts]
                return Called.gets(ids, incr)

        SAMPLE = list(range(20))
        Called.call_count = 0

        ncs = [NC(i) for i in SAMPLE]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].p(9) for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        ps = [ncs[0].p(2), ncs[1].p(9), ncs[2].p(9)]
        self.assertEqual(Called.call_count, 4)

        ps2 = [nc.p(2) for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        [nc.p(9) for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        [nc.p(2) for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        ps3 = [nc.p(i) for nc, i in zip(ncs, SAMPLE)]
        self.assertEqual(Called.call_count, 22)

        ps4 = [nc.p(i) for nc, i in zip(ncs, SAMPLE)]
        self.assertEqual(Called.call_count, 22)

        self.assertEqual(ps, [2, 10, 11])
        self.assertEqual(ps2, [(i + 2) for i in SAMPLE])
        self.assertEqual(ps3, [(i + i) for i in SAMPLE])
        self.assertEqual(ps3, ps4)
        self.assertEqual([(n.a + 1) for n in ncs], NC.get_ps(ncs, 1))

        with self.assertRaises(NError):

            @n_class  # noqa pylint: disable=C,W
            class NC2(object):
                def __init__(self, a):
                    self.a = a

                def __repr__(self):
                    return 'NC2(a=%s)' % self.a

                q = n_method()

                @q
                @classmethod
                def get_qs(cls, insts, incr):
                    ids = [self.a for self in insts]
                    return Called.gets(ids, incr)

        with self.assertRaises(NError):

            @n_class  # noqa pylint: disable=C,W
            class NC2(object):
                def __init__(self, a):
                    self.a = a

                def __repr__(self):
                    return 'NC3(a=%s)' % self.a

                @n_method
                def q(insts, incr):
                    ids = [self.a for self in insts]
                    return Called.gets(ids, incr)

        with self.assertRaises(NError):

            @n_class  # noqa pylint: disable=C,W
            class NC3(object):
                def __init__(self, a):
                    self.a = a

                def __repr__(self):
                    return 'NC3(a=%s)' % self.a

                q = n_method(accept_argument=accept_argument())

                @q
                @classmethod
                def get_qs(cls, insts, incr):
                    ids = [self.a for self in insts]
                    return Called.gets(ids, incr)

        with self.assertRaises(NError):

            @n_class  # noqa pylint: disable=C,W
            class NC4(object):
                def __init__(self, a):
                    self.a = a

                def __repr__(self):
                    return 'NC4(a=%s)' % self.a

                q = n_method(accept_argument=accept_argument(int, a=object, b=object))

                @q
                @classmethod
                def get_qs(cls, insts, incr):
                    ids = [self.a for self in insts]
                    return Called.gets(ids, incr)

        with self.assertRaises(NError):

            @n_class  # noqa pylint: disable=C,W
            class NC5(object):
                def __init__(self, a):
                    self.a = a

                def __repr__(self):
                    return 'NC5(a=%s)' % self.a

                q = n_method(accept_argument=accept_argument(a=int, c=int))

                @q
                @classmethod
                def get_qs(cls, insts, a=1, b=2):
                    ids = [self.a for self in insts]
                    return Called.gets(ids, a + b)

    def test_n_method_mismatch(self):
        @n_class
        class NC(object):
            def __init__(self, a):
                self.a = a

            def __repr__(self):
                return 'NC(a=%s)' % self.a

            s = n_method(accept_argument=accept_argument(incr=int))

            @s.n_call
            @classmethod
            def get_ss(cls, insts, incr=0):
                return []

            t = n_method(accept_argument=accept_argument(int), fallback=3)

            @t.n_call
            @classmethod
            def get_ts(cls, insts, incr=0):
                return Called.gets([0], incr)

        SAMPLE = list(range(20))
        Called.call_count = 0

        ncs = [NC(i) for i in SAMPLE]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].t(1) for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        _ts = [nc.t(1) for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        ss = [nc.s(incr=2) for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        ts = [nc.t(2) for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        self.assertEqual(ss, [None] * len(ss))
        self.assertEqual(ts, [2] + [3] * (len(ts) - 1))

    def test_n_property_sub(self):
        '''
        继承后有效
        '''

        @n_class
        class NMixin(object):
            def __init__(self, a):
                self.a = a

            def __repr__(self):
                return 'NC(a=%s)' % self.a

            p = n_method()

            @p.n_call
            @classmethod
            def get_ps(cls, insts, incr):
                ids = [self.a for self in insts]
                return Called.gets(ids, incr)

        class NC(NMixin):
            pass


        SAMPLE = list(range(20))
        Called.call_count = 0

        ncs = [NC(i) for i in SAMPLE]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].p(1) for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        ps = [nc.p(1) for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        self.assertEqual(ps, [(i + 1) for i in SAMPLE])

    def test_n_property_mix(self):
        '''
        一种极端情况，多种对象在同一行被创建，prefetch相互不应影响
        '''

        @n_class
        class NMixin(object):
            def __init__(self, a):
                self.a = a

            def __repr__(self):
                return 'NC(a=%s)' % self.a

            p = n_method()

            @p.n_call
            @classmethod
            def get_ps(cls, insts, incr):
                ids = [self.a for self in insts]
                return Called.gets(ids, incr)


        class NC1(NMixin):
            pass


        class NC2(NMixin):
            pass


        SAMPLE = range(20)
        Called.call_count = 0

        ncs = [cls(i) for i in SAMPLE for cls in (NC1, NC2)]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].p(1) for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        [ncs[1].p(1) for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        ps = [nc.p(1) for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        group_sample = [(i + 1) for i in SAMPLE for cls in (NC1, NC2)]
        self.assertEqual(ps, group_sample)


class Called(object):
    call_count = 0

    @classmethod
    def get(cls, i, incr):
        cls.call_count += 1
        return i + incr

    @classmethod
    def gets(cls, ids, incr):
        cls.call_count += 1
        return [(i + incr) for i in ids]
