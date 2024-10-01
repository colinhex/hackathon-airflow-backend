import asyncio
from typing import List, Dict

from airflow.providers.openai.hooks.openai import OpenAIHook
from openai import OpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ParsedChatCompletion
from typing_extensions import Tuple

from unibas.common.environment.variables import OpenAiEnvVariables
from unibas.common.logic.logic_math import create_distance_dataframe, sequence_matcher_distance
from unibas.common.model.model_job import Job
from unibas.common.model.model_openai import OpenAiFeatureResponse
from unibas.common.model.model_parsed import ParsedContent, ParsedHtml, HtmlAttributes, UrlParseResult
from unibas.common.model.model_prompt import *


def openai_get_client() -> OpenAI:
    if OpenAiEnvVariables.test_api_key is not None:
        return OpenAI(api_key=OpenAiEnvVariables.test_api_key)
    return OpenAIHook(conn_id=OpenAiEnvVariables.conn_id).get_conn()


def get_chunks(job: Job):
    chunks = []
    chunk_mapping = {}
    global_chunk_index = 0
    for resource in job.resources:
        for chunk in resource.content:
            chunk_mapping[global_chunk_index] = str(resource.id)
            chunks.append(chunk)
            global_chunk_index += 1
    return chunks, chunk_mapping


def collect_response_data(chunk_data, chunk_mapping):
    collection = {}
    for mapping_index, data in chunk_data:
        resource_id = chunk_mapping[mapping_index]
        collection.setdefault(resource_id, []).append(data)
    return collection


def create_embeddings(chunks: List[str]) -> List[Tuple[int, List[float]]]:
    response: CreateEmbeddingResponse = openai_get_client().embeddings.create(
        input=chunks,
        model=OpenAiEnvVariables.embedding_model
    )
    return [(embedding.index, embedding.embedding) for embedding in response.data]


def create_embeddings_for_job(job: Job) -> Dict[str, List[List[float]]]:
    assert all([isinstance(resource, ParsedContent) for resource in job.resources])
    chunks, chunk_mapping = get_chunks(job)
    embeddings = create_embeddings(chunks)
    return collect_response_data(embeddings, chunk_mapping)


def create_features_for_job(job: Job) -> Dict[str, List[Dict]]:
    assert all([isinstance(resource, ParsedContent) for resource in job.resources])
    chunks, chunk_mapping = get_chunks(job)
    features = asyncio.run(get_features(chunks))
    return collect_response_data(features, chunk_mapping)


async def get_features(chunks: List[str]) -> List[Tuple[int, Dict]]:
    oai_client = openai_get_client()

    async def send_feature_request(client: OpenAI, index: int, chunk: str):
        print(f'Outgoing Request: Sending request for chunk index {index}')
        parsed_completion: ParsedChatCompletion = await asyncio.to_thread(
            client.beta.chat.completions.parse,
            model=OpenAiEnvVariables.llm_model,
            messages=create_feature_extraction_messages(chunk),
            response_format=OpenAiFeatureResponse,
        )
        print(f'Incoming Response: Received response chunk index {index}')
        return index, clean_llm_tag_choices(OpenAiFeatureResponse.parse_raw(parsed_completion.choices[0].message.content)).model_dump()

    features = await asyncio.gather(*[send_feature_request(oai_client, idx, feature) for idx, feature in enumerate(chunks)])
    return [(feature_index, feature) for feature_index, feature in sorted(features, key=lambda x: x[0])]


def clean_llm_tag_choice(choices, options, distance_function):
    df = create_distance_dataframe(choices, options, distance_function)
    cleaned_list = []

    for idx, row in df.iterrows():
        sorted_row = row.sort_values(ascending=False)
        value, score = (sorted_row.index[0], sorted_row.iloc[0]) if not sorted_row.empty else (None, None)
        if score is not None and score > 0.9:  # Accept slight errors like capitalization / spelling / punctuation differences
            cleaned_list.append(value)

    return cleaned_list


def clean_llm_tag_choices(feature_response: OpenAiFeatureResponse):
    """
    Clean the LLM tag choices in the feature response.
    """
    if feature_response.intended_audience:
        feature_response.intended_audience = clean_llm_tag_choice(
            feature_response.intended_audience, INTENDED_AUDIENCE, sequence_matcher_distance
        )

    if feature_response.departments:
        feature_response.departments = clean_llm_tag_choice(
            feature_response.departments, DEPARTMENTS, sequence_matcher_distance
        )

    if feature_response.faculties:
        feature_response.faculties = clean_llm_tag_choice(
            feature_response.faculties, FACULTIES, sequence_matcher_distance
        )

    if feature_response.administrative_services:
        feature_response.administrative_services = clean_llm_tag_choice(
            feature_response.administrative_services, ADMINISTRATIVE_SERVICES, sequence_matcher_distance
        )

    if feature_response.degree_levels:
        feature_response.degree_levels = clean_llm_tag_choice(
            feature_response.degree_levels, DEGREE_LEVELS, sequence_matcher_distance
        )

    if feature_response.topics:
        feature_response.topics = clean_llm_tag_choice(
            feature_response.topics, TOPICS, sequence_matcher_distance
        )

    if feature_response.information_type:
        feature_response.information_type = clean_llm_tag_choice(
            feature_response.information_type, INFORMATION_TYPE, sequence_matcher_distance
        )

    return feature_response