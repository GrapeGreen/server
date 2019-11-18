import unittest
import unittest.mock
import numpy
import server


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.cache = unittest.mock.MagicMock()
        self.db = unittest.mock.MagicMock()
        self.kvs = server.KeyValueStorage(self.cache, self.db)

    def test_get_from_cache(self):
        key = 10
        self.cache.exists.return_value = True
        self.cache.get.return_value = 10
        self.assertEqual(self.kvs.get(key), 10)
        self.cache.exists.assert_called_with(key)
        self.db.find_one.assert_not_called()

    def test_get_from_db(self):
        key, value = 10, 10
        self.cache.exists.return_value = False
        self.db.find_one.return_value = {'value' : value}
        self.assertEqual(self.kvs.get(key), value)
        self.cache.exists.assert_called_with(key)
        self.db.find_one.assert_called()
        self.cache.set.assert_called_with(key, value)

    def test_get_none(self):
        key = 10
        self.cache.exists.return_value = False
        self.db.find_one.return_value = None
        self.assertEqual(self.kvs.get(key), None)
        self.cache.exists.assert_called_with(key)
        self.db.find_one.assert_called()
        self.cache.set.assert_not_called()

    def test_delete_exists(self):
        key = 10
        self.cache.exists.return_value = True
        self.assertTrue(self.kvs.delete(key))
        self.cache.delete.assert_called_with(key)

    def test_delete_not_exists(self):
        key = 10
        self.cache.exists.return_value = False
        self.assertFalse(self.kvs.delete(key))
        self.cache.delete.assert_not_called()

    def test_put_not_exists(self):
        key, value = 10, 10
        self.cache.exists.return_value = False
        self.assertFalse(self.kvs.put(key, value))
        self.cache.set.assert_called_with(key, value)

    def test_put_not_exists(self):
        key, value = 10, 10
        self.cache.exists.return_value = True
        self.assertTrue(self.kvs.put(key, value))
        self.cache.set.assert_called_with(key, value)

    def tearDown(self):
        del self.cache
        del self.db
        del self.kvs


unittest.main()

