from collections import defaultdict
from datetime import datetime
from time import time
from typing import Any, List, Callable, Iterable

from toolz import partition_all

__HEADER_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


class StopWatch:
    start: float = time()

    def stop(self) -> float:
        return time() - self.start


def iso_format_from_l_mod_header_if_present(dt: datetime | str | None) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, str):
        return datetime.strptime(dt, __HEADER_DATE_FORMAT).isoformat()


def list_if_not(data: Any) -> List[Any]:
    return [data] if not isinstance(data, list) else data


def vectorize(foo: Callable[[Any], Any]) -> Callable[[List[Any]], Any]:
    return lambda xs: list(map(foo, xs))


def deep_merge_on_field(dict_x, dictionary, field):
    for i, inner_dictionary in dictionary.items():
        for j, v in inner_dictionary.items():
            dict_x[i][j].update({field: v})


def deep_merge(texts, tags, embeddings):
    dict_x = defaultdict(lambda: defaultdict(dict))
    deep_merge_on_field(dict_x, texts, 'text')
    deep_merge_on_field(dict_x, embeddings, 'embedding')
    deep_merge_on_field(dict_x, tags, 'tags')
    dict_x = {i: dict(inner_dict) for i, inner_dict in dict_x.items()}
    return dict_x


async def async_partition(elements: Iterable[Any], partition_size: int):
    partitions = partition_all(partition_size, elements)
    for part in partitions:
        yield part