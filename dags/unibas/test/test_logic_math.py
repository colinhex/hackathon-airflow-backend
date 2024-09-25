import unittest

from unibas.common.logic.logic_math import create_distance_dataframe, sequence_matcher_distance


class TestMathLogic(unittest.TestCase):

    def test_create_distance_dataframe_correctness(self):
        list1 = ["apple", "banana"]
        list2 = ["apple", "orange"]
        df = create_distance_dataframe(list1, list2, sequence_matcher_distance)
        self.assertEqual(df.loc["apple", "apple"], 1.0)
        self.assertLess(df.loc["banana", "orange"], 1.0)

    def test_create_distance_dataframe_empty_lists(self):
        list1 = []
        list2 = []
        df = create_distance_dataframe(list1, list2, sequence_matcher_distance)
        self.assertTrue(df.empty)

    def test_create_distance_dataframe_mismatched_lists(self):
        list1 = ["apple"]
        list2 = ["apple", "orange"]
        df = create_distance_dataframe(list1, list2, sequence_matcher_distance)
        self.assertEqual(df.loc["apple", "apple"], 1.0)
        self.assertLess(df.loc["apple", "orange"], 1.0)

    def test_sequence_matcher_distance_identical_strings(self):
        self.assertEqual(sequence_matcher_distance("test", "test"), 1.0)

    def test_sequence_matcher_distance_completely_different_strings(self):
        self.assertEqual(sequence_matcher_distance("test", "abcd"), 0.0)

    def test_sequence_matcher_distance_partial_match(self):
        self.assertGreater(sequence_matcher_distance("test", "testing"), 0.5)


if __name__ == '__main__':
    unittest.main()
