from difflib import SequenceMatcher

import pandas as pd
from typing_extensions import List, Callable


def create_distance_dataframe(
        list1: List[str],
        list2: List[str],
        distance_func: Callable[[str, str], float]
) -> pd.DataFrame:
    df = pd.DataFrame(index=list1, columns=list2)

    for y in list1:
        for x in list2:
            df.loc[y, x] = distance_func(y, x)

    return df


def sequence_matcher_distance(s1: str, s2: str) -> float:
    return SequenceMatcher(None, s1, s2).ratio()