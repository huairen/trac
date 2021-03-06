# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

import os
import unittest

from trac.config import ConfigurationError
from trac.env import Environment
from trac.test import MockRequest, mkdtemp
from trac.tests.compat import rmtree
from trac.util import translation


class DatabaseFileTestCase(unittest.TestCase):

    def setUp(self):
        self.env_path = mkdtemp()
        self.db_path = os.path.join(self.env_path, 'db', 'trac.db')

    def tearDown(self):
        rmtree(self.env_path)

    def _create_env(self):
        env = Environment(self.env_path, create=True)
        env.shutdown()

    def _db_query(self, env):
        env.db_query("SELECT name FROM system")

    def test_missing_tracdb(self):
        self._create_env()
        os.remove(self.db_path)
        env = Environment(self.env_path)
        try:
            self._db_query(env)
            self.fail('ConfigurationError not raised')
        except ConfigurationError as e:
            self.assertIn('Database "', unicode(e))
            self.assertIn('" not found.', unicode(e))

    def test_no_permissions(self):
        self._create_env()
        os.chmod(self.db_path, 0444)
        env = Environment(self.env_path)
        try:
            self._db_query(env)
            self.fail('ConfigurationError not raised')
        except ConfigurationError as e:
            self.assertIn('requires read _and_ write permissions', unicode(e))

    if os.name == 'posix' and os.getuid() == 0:
        del test_no_permissions  # For root, os.access() always returns True

    def test_error_with_lazy_translation(self):
        self._create_env()
        os.remove(self.db_path)
        env = Environment(self.env_path)
        req = MockRequest(env, authname='trac_auth=1234567890')
        translation.make_activable(lambda: req.locale, env.path)
        try:
            self._db_query(env)
            self.fail('ConfigurationError not raised')
        except ConfigurationError as e:
            message = unicode(e)
            self.assertIn('Database "', message)
            self.assertIn('" not found.', message)
        finally:
            translation.deactivate()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DatabaseFileTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
