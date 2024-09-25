import unittest
from unibas.common.logic.logic_utility import transform_nested


class TestTransformNested(unittest.TestCase):
    def test_transform_nested_dict(self):
        data = {'a': 1, 'b': {'c': 2, 'd': 3}}
        transform_func = lambda x: x * 2
        target_type = int
        expected = {'a': 2, 'b': {'c': 4, 'd': 6}}

        result = transform_nested(data, transform_func, target_type)
        self.assertEqual(result, expected)

    def test_transform_nested_list(self):
        data = [1, [2, 3], 4]
        transform_func = lambda x: x * 2
        target_type = int
        expected = [2, [4, 6], 8]

        result = transform_nested(data, transform_func, target_type)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()