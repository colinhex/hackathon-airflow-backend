from typing import Iterable, Union, Dict, List, Callable

from toolz import partition_all
from typing_extensions import Any, AsyncGenerator


async def async_partition(elements: Iterable[Any], partition_size: int) -> AsyncGenerator[Any, None]:
    """
    Asynchronously partition an iterable into chunks of a specified size.

    Args:
        elements (Iterable[Any]): The iterable to partition.
        partition_size (int): The size of each partition.

    Yields:
        AsyncGenerator[Any, None]: An asynchronous generator yielding partitions of the specified size.
    """
    partitions = partition_all(partition_size, elements)
    for part in partitions:
        yield part


def transform_nested(
        data: Union[Dict[str, Any], List[Any]],
        transform_func: Callable[[Any], Any],
        target_type: type
) -> Union[Dict[str, Any], List[Any]]:
    """
    Recursively transform elements of a specified type within a nested dictionary or list.

    Args:
        data (Union[Dict[str, Any], List[Any]]): The nested dictionary or list to transform.
        transform_func (Callable[[Any], Any]): The function to apply to elements of the target type.
        target_type (type): The type of elements to transform.

    Returns:
        Union[Dict[str, Any], List[Any]]: The transformed nested dictionary or list.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                data[key] = transform_nested(value, transform_func, target_type)
            elif isinstance(value, target_type):
                data[key] = transform_func(value)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            if isinstance(value, (dict, list)):
                data[index] = transform_nested(value, transform_func, target_type)
            elif isinstance(value, target_type):
                data[index] = transform_func(value)
    return data