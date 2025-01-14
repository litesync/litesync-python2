#-*- coding: ISO-8859-1 -*-
# litesync/test/hooks.py: tests for various SQLite-specific hooks
#
# Copyright (C) 2006-2015 Gerhard H�ring <gh@ghaering.de>
#
# This file is part of pysqlite.
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

import unittest
import litesync.dbapi2 as sqlite

class CollationTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def CheckCreateCollationNotCallable(self):
        con = sqlite.connect(":memory:")
        try:
            con.create_collation("X", 42)
            self.fail("should have raised a TypeError")
        except TypeError, e:
            self.assertEqual(e.args[0], "parameter must be callable")

    def CheckCreateCollationNotAscii(self):
        con = sqlite.connect(":memory:")
        try:
            con.create_collation("coll�", cmp)
            self.fail("should have raised a ProgrammingError")
        except sqlite.ProgrammingError, e:
            pass

    def CheckCollationIsUsed(self):
        def mycoll(x, y):
            # reverse order
            return -cmp(x, y)

        con = sqlite.connect(":memory:")
        con.create_collation("mycoll", mycoll)
        sql = """
            select x from (
            select 'a' as x
            union
            select 'b' as x
            union
            select 'c' as x
            ) order by x collate mycoll
            """
        result = con.execute(sql).fetchall()
        if result[0][0] != "c" or result[1][0] != "b" or result[2][0] != "a":
            self.fail("the expected order was not returned")

        con.create_collation("mycoll", None)
        try:
            result = con.execute(sql).fetchall()
            self.fail("should have raised an OperationalError")
        except sqlite.OperationalError, e:
            self.assertEqual(e.args[0].lower(), "no such collation sequence: mycoll")

    def CheckCollationReturnsLargeInteger(self):
        def mycoll(x, y):
            # reverse order
            return -((x > y) - (x < y)) * 2**32
        con = sqlite.connect(":memory:")
        con.create_collation("mycoll", mycoll)
        sql = """
            select x from (
            select 'a' as x
            union
            select 'b' as x
            union
            select 'c' as x
            ) order by x collate mycoll
            """
        result = con.execute(sql).fetchall()
        self.assertEqual(result, [('c',), ('b',), ('a',)],
                         msg="the expected order was not returned")

    def CheckCollationRegisterTwice(self):
        """
        Register two different collation functions under the same name.
        Verify that the last one is actually used.
        """
        con = sqlite.connect(":memory:")
        con.create_collation("mycoll", cmp)
        con.create_collation("mycoll", lambda x, y: -cmp(x, y))
        result = con.execute("""
            select x from (select 'a' as x union select 'b' as x) order by x collate mycoll
            """).fetchall()
        if result[0][0] != 'b' or result[1][0] != 'a':
            self.fail("wrong collation function is used")

    def CheckDeregisterCollation(self):
        """
        Register a collation, then deregister it. Make sure an error is raised if we try
        to use it.
        """
        con = sqlite.connect(":memory:")
        con.create_collation("mycoll", cmp)
        con.create_collation("mycoll", None)
        try:
            con.execute("select 'a' as x union select 'b' as x order by x collate mycoll")
            self.fail("should have raised an OperationalError")
        except sqlite.OperationalError, e:
            if not e.args[0].startswith("no such collation sequence"):
                self.fail("wrong OperationalError raised")

class ProgressTests(unittest.TestCase):
    def CheckProgressHandlerUsed(self):
        """
        Test that the progress handler is invoked once it is set.
        """
        con = sqlite.connect(":memory:")
        progress_calls = []
        def progress():
            progress_calls.append(None)
            return 0
        con.set_progress_handler(progress, 1)
        con.execute("""
            create table foo(a, b)
            """)
        self.assertTrue(progress_calls)


    def CheckCancelOperation(self):
        """
        Test that returning a non-zero value stops the operation in progress.
        """
        con = sqlite.connect(":memory:")
        progress_calls = []
        def progress():
            progress_calls.append(None)
            return 1
        con.set_progress_handler(progress, 1)
        curs = con.cursor()
        self.assertRaises(
            sqlite.OperationalError,
            curs.execute,
            "create table bar (a, b)")

    def CheckClearHandler(self):
        """
        Test that setting the progress handler to None clears the previously set handler.
        """
        con = sqlite.connect(":memory:")
        action = []
        def progress():
            action.append(1)
            return 0
        con.set_progress_handler(progress, 1)
        con.set_progress_handler(None, 1)
        con.execute("select 1 union select 2 union select 3").fetchall()
        self.assertEqual(len(action), 0, "progress handler was not cleared")

class LimitTests(unittest.TestCase):
    def CheckGetLimit(self):
        """
        Test that the get limit method return something useful.
        """
        con = sqlite.connect(":memory:")
        val = con.get_limit(sqlite.SQLITE_LIMIT_VARIABLE_NUMBER)
        self.assertTrue(val > 0)

    def CheckSetLimit(self):
        """
        Test that the set limit method actally changes limits.
        """
        con = sqlite.connect(":memory:")
        oldval = con.get_limit(sqlite.SQLITE_LIMIT_VARIABLE_NUMBER)
        con.set_limit(sqlite.SQLITE_LIMIT_VARIABLE_NUMBER, oldval - 1)
        newval = con.get_limit(sqlite.SQLITE_LIMIT_VARIABLE_NUMBER)

        self.assertEqual(newval, oldval - 1)

def suite():
    collation_suite = unittest.makeSuite(CollationTests, "Check")
    progress_suite = unittest.makeSuite(ProgressTests, "Check")
    limit_suite = unittest.makeSuite(LimitTests, "Check")
    return unittest.TestSuite((collation_suite, progress_suite, limit_suite))

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    test()
