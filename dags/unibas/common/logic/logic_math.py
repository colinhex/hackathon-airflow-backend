from difflib import SequenceMatcher

import pandas as pd
from typing_extensions import List, Callable


def create_distance_dataframe(
        list1: List[str],
        list2: List[str],
        distance_func: Callable[[str, str], float]
) -> pd.DataFrame:
    """
    Create a DataFrame containing the distances between elements of two lists.

    Args:
        list1 (List[str]): The first list of strings.
        list2 (List[str]): The second list of strings.
        distance_func (Callable[[str, str], float]): A function to calculate the distance between two strings.

    Returns:
        pd.DataFrame: A DataFrame where each cell (i, j) contains the distance between list1[i] and list2[j].
    """
    df = pd.DataFrame(index=list1, columns=list2)

    for y in list1:
        for x in list2:
            df.loc[y, x] = distance_func(y, x)

    return df


def sequence_matcher_distance(s1: str, s2: str) -> float:
    """
    Calculate the similarity ratio between two strings using SequenceMatcher.

    Args:
        s1 (str): The first string.
        s2 (str): The second string.

    Returns:
        float: The similarity ratio between the two strings.
    """
    return SequenceMatcher(None, s1, s2).ratio()