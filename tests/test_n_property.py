# -*- coding: utf-8 -*-
import unittest
from n_property import n_class, n_property, NError


class NClassTestCase(unittest.TestCase):
    def test_n_property(self):
        @n_class
        class NC(object):
            def __init__(self, a):
                self.a = a

            def __repr__(self):
                return 'NC(a=%s)' % self.a

            @n_property
            def p(selfs):
                ids = [self.a for self in selfs]
                return Called.gets(ids)

            q = n_property()

            @q.n_getter
            @classmethod
            def get_qs(cls, insts):
                ids = [self.a for self in insts]
                return Called.gets(ids)


        SAMPLE = range(20)
        Called.call_count = 0

        ncs = [NC(i) for i in SAMPLE]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].p for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        ps = [nc.p for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        qs = [nc.q for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        self.assertEqual(ps, SAMPLE)
        self.assertEqual(qs, SAMPLE)
        self.assertEqual([n.a for n in ncs], NC.get_qs(ncs))

        with self.assertRaises(NError):

            @n_class  # noqa pylint: disable=C,W
            class NC_(object):
                def __init__(self, a):
                    self.a = a

                def __repr__(self):
                    return 'NC(a=%s)' % self.a

                q = n_property()

                @q
                @classmethod
                def get_qs(cls, insts):
                    ids = [self.a for self in insts]
                    return Called.gets(ids)

    def test_n_property_mismatch(self):
        @n_class
        class NC(object):
            def __init__(self, a):
                self.a = a

            def __repr__(self):
                return 'NC(a=%s)' % self.a

            @n_property
            def p(selfs):
                return Called.gets([0])

            @n_property(1)
            def q(selfs):
                return []

            @n_property(2)
            def r(selfs):
                return Called.gets([0])

            s = n_property()

            @s.n_getter
            @classmethod
            def get_ss(cls, insts):
                return []

            t = n_property(3)

            @t.n_getter
            @classmethod
            def get_ts(cls, insts):
                return Called.gets([0])

        SAMPLE = range(20)
        Called.call_count = 0

        ncs = [NC(i) for i in SAMPLE]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].p for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        ps = [nc.p for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        qs = [nc.q for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        rs = [nc.r for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        ss = [nc.s for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        ts = [nc.t for nc in ncs]
        self.assertEqual(Called.call_count, 6)

        self.assertEqual(ps, [0] + [None] * (len(ps) - 1))
        self.assertEqual(qs, [1] * len(qs))
        self.assertEqual(rs, [0] + [2] * (len(rs) - 1))
        self.assertEqual(ss, [None] * len(ss))
        self.assertEqual(ts, [0] + [3] * (len(ts) - 1))

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

            @n_property
            def p(selfs):
                ids = [self.a for self in selfs]
                return Called.gets(ids)

        class NC(NMixin):
            pass


        SAMPLE = range(20)
        Called.call_count = 0

        ncs = [NC(i) for i in SAMPLE]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].p for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        ps = [nc.p for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        self.assertEqual(ps, SAMPLE)

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

            @n_property
            def p(selfs):
                ids = [self.a for self in selfs]
                return Called.gets(ids)


        class NC1(NMixin):
            pass


        class NC2(NMixin):
            pass


        SAMPLE = range(20)
        Called.call_count = 0

        ncs = [cls(i) for i in SAMPLE for cls in (NC1, NC2)]
        self.assertEqual(Called.call_count, 0)

        [ncs[0].p for nc in ncs]
        self.assertEqual(Called.call_count, 1)

        [ncs[1].p for nc in ncs]
        self.assertEqual(Called.call_count, 2)

        ps = [nc.p for nc in ncs]
        self.assertEqual(Called.call_count, 4)

        group_sample = [i for i in SAMPLE for cls in (NC1, NC2)]
        self.assertEqual(ps, group_sample)


class Called(object):
    call_count = 0

    @classmethod
    def get(cls, i):
        cls.call_count += 1
        return i

    @classmethod
    def gets(cls, ids):
        cls.call_count += 1
        return ids
