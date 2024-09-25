import asyncio
import unittest

from unibas.common.misc import async_partition


class TestAsyncPartition(unittest.TestCase):
    def test_async_partition(self):
        async def run_test():
            elements = [1, 2, 3, 4, 5]
            partition_size = 2
            expected_partitions = [(1, 2), (3, 4), (5,)]

            result = []
            async for part in async_partition(elements, partition_size):
                result.append(part)

            self.assertEqual(expected_partitions, result)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()