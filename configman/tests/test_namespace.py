# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is configman
#
# The Initial Developer of the Original Code is
# Mozilla Foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    K Lars Lohn, lars@mozilla.com
#    Peter Bengtsson, peterbe@mozilla.com
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import unittest
import datetime
import functools

import configman.config_manager as config_manager
import configman.datetime_util as dtu

from configman.option import Option
from configman.orderedset import OrderedSet


#==============================================================================
class TestCase(unittest.TestCase):

    #--------------------------------------------------------------------------
    def test_Namespace_basics(self):
        namespace = config_manager.Namespace('doc string')
        namespace.alpha = 1
        my_birthday = datetime.datetime(1960, 5, 4, 15, 10)
        namespace.beta = my_birthday
        self.assertEqual(namespace.alpha.name, 'alpha')
        self.assertEqual(namespace.alpha.doc, None)
        self.assertEqual(namespace.alpha.default, 1)
        self.assertEqual(namespace.alpha.from_string_converter, int)
        self.assertEqual(namespace.alpha.value, 1)
        self.assertEqual(namespace.beta.name, 'beta')
        self.assertEqual(namespace.beta.doc, None)
        self.assertEqual(namespace.beta.default, my_birthday)
        self.assertEqual(
            namespace.beta.from_string_converter,
            dtu.datetime_from_ISO_string
        )
        self.assertEqual(namespace.beta.value, my_birthday)

    #--------------------------------------------------------------------------
    def test_configuration_with_namespace(self):
        namespace = config_manager.Namespace()
        namespace.add_option('a')
        namespace.a.default = 1
        namespace.a.doc = 'the a'
        namespace.b = 17
        config = config_manager.ConfigurationManager(
            [namespace],
            argv_source=[]
        )
        self.assertTrue(
            isinstance(config.option_definitions.b, config_manager.Option)
        )
        self.assertEqual(config.option_definitions.b.value, 17)
        self.assertEqual(config.option_definitions.b.default, 17)
        self.assertEqual(config.option_definitions.b.name, 'b')

    #--------------------------------------------------------------------------
    def test_namespace_constructor_3(self):
        """test json definition"""

        j = '{ "a": {"name": "a", "default": 1, "doc": "the a"}, "b": 17}'
        config = config_manager.ConfigurationManager(
            [j],
            argv_source=[]
        )
        self.assertTrue(
            isinstance(config.option_definitions.a,  config_manager.Option)
        )
        self.assertEqual(config.option_definitions.a.value, 1)
        self.assertEqual(config.option_definitions.a.default, 1)
        self.assertEqual(config.option_definitions.a.name, 'a')
        self.assertTrue(
            isinstance(config.option_definitions.b, config_manager.Option)
        )
        self.assertEqual(config.option_definitions.b.value, 17)
        self.assertEqual(config.option_definitions.b.default, 17)
        self.assertEqual(config.option_definitions.b.name, 'b')

    #--------------------------------------------------------------------------
    def test_namespace_from_json_with_default_datetime_date(self):
        """fix that verifies this bug
        https://github.com/twobraids/configman/issues/7
        """
        j = (
            u'{"bday": {"default": "1979-12-13", "name": "bday",'
            u' "from_string_converter": "configman.datetime_util.date_from_ISO'
            u'_string", "doc": null, "value": "1979-12-13", '
            u'"short_form": null}}'
        )
        config = config_manager.ConfigurationManager(
            [j],
            [],
            use_auto_help=False,
            use_admin_controls=True,
            argv_source=[]
        )

        option = config_manager.Option(
            'bday',
            default="1979-12-13",
        )
        self.assertEqual(
            config.option_definitions.bday.default,
            option.default
        )

    #--------------------------------------------------------------------------
    def test_walk_expanding_class_options(self):
        class A(config_manager.RequiredConfig):
            required_config = {
                'a': config_manager.Option('a', 1, 'the a'),
                'b': 17,
            }
        n = config_manager.Namespace()
        n.source = config_manager.Namespace()
        n.source.add_option('c', A, 'the A class')
        assert n.source.c.doc == 'the A class'

        n.dest = config_manager.Namespace()
        n.dest.add_option('c', A, doc='the A class')
        assert n.dest.c.doc == 'the A class'
        c = config_manager.ConfigurationManager(
            [n],
            use_admin_controls=False,
            use_auto_help=False,
            argv_source=[]
        )
        e = config_manager.Namespace()
        e.s = config_manager.Namespace()
        e.s.add_option('c', A, doc='the A class')
        e.s.add_option('a', 1, 'the a')
        e.s.add_option('b', default=17)
        e.d = config_manager.Namespace()
        e.d.add_option('c', A, doc='the A class')
        e.d.add_option('a', 1, 'the a')
        e.d.add_option('b', default=17)

    #--------------------------------------------------------------------------
        def namespace_test(val):
            self.assertEqual(type(val), config_manager.Namespace)

    #--------------------------------------------------------------------------
        def option_test(val, expected=None):
            self.assertEqual(val.name, expected.name)
            self.assertEqual(val.default, expected.default)
            self.assertEqual(val.doc, expected.doc)

        e = [
            ('dest', namespace_test),
            ('dest.a', functools.partial(option_test, expected=e.d.a)),
            ('dest.b', functools.partial(option_test, expected=e.d.b)),
            ('dest.c', functools.partial(option_test, expected=e.d.c)),
            ('source', namespace_test),
            ('source.a', functools.partial(option_test, expected=e.s.a)),
            ('source.b', functools.partial(option_test, expected=e.s.b)),
            ('source.c', functools.partial(option_test, expected=e.s.c)),
        ]

        #c_contents = [(qkey, key, val) for qkey, key, val in c._walk_config()]
        c_contents = [(qkey, c.option_definitions[qkey])
                      for qkey in c.option_definitions.keys_breadth_first(
                          include_dicts=True
                      )]
        c_contents.sort()
        e.sort()
        for c_tuple, e_tuple in zip(c_contents, e):
            qkey, val = c_tuple
            e_qkey, e_fn = e_tuple
            self.assertEqual(qkey, e_qkey)
            e_fn(val)

    #--------------------------------------------------------------------------
    def test_setting_nested_namespaces(self):
        n = config_manager.Namespace()
        n.namespace('sub')
        sub_n = n.sub
        sub_n.add_option('name')
        self.assertTrue(n.sub)
        self.assertTrue(isinstance(n.sub.name, config_manager.Option))

    #--------------------------------------------------------------------------
    def test_editing_values_on_namespace(self):
        n = config_manager.Namespace()
        self.assertRaises(KeyError, n.set_value, 'name', 'Peter')
        n.add_option('name', 'Lars')
        n.set_value('name', 'Peter')
        self.assertTrue(n.name)
        self.assertEqual(n.name.value, 'Peter')
        n.namespace('user')
        n.user.add_option('age', 100)
        n.set_value('user.age', 200)
        self.assertTrue(n.user.age)
        self.assertEqual(n.user.age.value, 200)

        # let's not be strict once
        n.set_value('user.gender', u'male', strict=False)
        self.assertEqual(n.user.gender.value, u'male')

    #--------------------------------------------------------------------------
    def test_comparing_namespace_instances(self):
        n = config_manager.Namespace()
        n2 = config_manager.Namespace()
        self.assertEqual(n, n2)

        n3 = config_manager.Namespace()
        n3.add_option('name', 'Peter')
        self.assertNotEqual(n, n3)

        n2.add_option('name', 'Peter', 'Name of a person')
        self.assertNotEqual(n, n2)
        self.assertNotEqual(n2, n3)

        n4 = config_manager.Namespace()
        n4.add_option('name', 'Peter')
        self.assertEqual(n4, n3)

    #--------------------------------------------------------------------------
    def test_deep_copy(self):
        from copy import deepcopy

        n = config_manager.Namespace()
        n2 = deepcopy(n)
        self.assertTrue(n is not n2)

        n = config_manager.Namespace()
        n.add_option('name', 'Peter')
        n3 = deepcopy(n)
        self.assertEqual(n, n3)
        self.assertTrue(n.name is not n3.name)

        def foo(all, local, args):
            return 17
        n = config_manager.Namespace()
        n.add_aggregation('a', foo)
        n4 = deepcopy(n)
        self.assertTrue(n.a is not n4.a)

    #--------------------------------------------------------------------------
    def test_add_option_with_option(self):
        o = Option('dwight')
        n = config_manager.Namespace()
        n.add_option(o)
        self.assertTrue(o is n.dwight)

    #--------------------------------------------------------------------------
    def test_verify_key_order(self):
        d = config_manager.Namespace()
        d.add_option('a.b.c')
        d.a.b.add_option('d')
        d.a.add_option('x')
        d.add_aggregation('b', lambda x, y, z: None)
        self.assertTrue(isinstance(d._key_order, OrderedSet))
        # the keys should be in order of insertion within each level of the
        # nested dicts
        keys_in_breadth_first_order = [
            'a', 'b', 'a.b', 'a.x', 'a.b.c', 'a.b.d'
        ]
        self.assertEqual(
            keys_in_breadth_first_order,
            [k for k in d.keys_breadth_first(include_dicts=True)]
        )

