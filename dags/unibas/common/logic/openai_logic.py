import asyncio
from io import BytesIO
from typing import List

from airflow.providers.openai.hooks.openai import OpenAIHook
from openai import OpenAI
from openai.types import CreateEmbeddingResponse, FileObject, Batch
from openai.types.chat import ParsedChatCompletion
from typing_extensions import Dict, Tuple

from unibas.common.constants import OpenAi
from unibas.common.logic.math_logic import create_distance_dataframe, sequence_matcher_distance
from unibas.common.model.oai_model import OpenAiEmbeddings, OpenAiEmbedding, OpenAiBatchCompletionEntry, \
    OpenAiFeatureResponse
from unibas.common.model.parsed_model import TextChunks
from unibas.common.model.prompt_model import create_feature_extraction_messages, FACULTIES, INTENDED_AUDIENCE, \
    DEPARTMENTS, ADMINISTRATIVE_SERVICES, DEGREE_LEVELS, TOPICS, INFORMATION_TYPE


def openai_get_client() -> OpenAI:
    return OpenAIHook(conn_id=OpenAi.conn_id).get_conn()


def get_embeddings(query: OpenAiEmbeddings) -> OpenAiEmbeddings:
    response: CreateEmbeddingResponse = openai_get_client().embeddings.create(
        input=query.get_ordered_text_chunks(),
        model=query.embedding_model,
    )
    return collect_embeddings(query, response)


def get_embeddings_from_text_chunks(text_chunks: TextChunks, embedding_model=OpenAi.embedding_model) -> OpenAiEmbeddings:
    return get_embeddings(embeddings_query_from_text_chunks(text_chunks, embedding_model=embedding_model))


def collect_embeddings(embeddings: OpenAiEmbeddings, response: CreateEmbeddingResponse) -> OpenAiEmbeddings:
    indexed_embeddings = {e.chunk_index: e for e in embeddings.embeddings}

    final_embeddings = OpenAiEmbeddings()
    for _response in response.data:
        index_embedding = indexed_embeddings[_response.index]
        final_embeddings.embeddings.append(
            OpenAiEmbedding(chunk_index=index_embedding.chunk_index, text_chunk=index_embedding.text_chunk, embedding=_response.embedding)
        )
    return final_embeddings


def embedding_query_from_text_chunk(chunk_index: int, text_chunk: str, embeddings_model: str = OpenAi.embedding_model) -> OpenAiEmbedding:
    return OpenAiEmbedding(chunk_index=chunk_index, text_chunk=text_chunk, embedding_model=embeddings_model)


def embeddings_query_from_text_chunks(text_chunks: TextChunks, embedding_model: str = OpenAi.embedding_model) -> OpenAiEmbeddings:
    batch_embeddings_query = OpenAiEmbeddings(embedding_model=embedding_model)
    for chunk_index, text_chunk in text_chunks.items():
        batch_embeddings_query.embeddings.append(
            embedding_query_from_text_chunk(chunk_index=chunk_index, text_chunk=text_chunk)
        )
    return batch_embeddings_query


def get_feature_extractions_via_batch_api(text_chunks: TextChunks) -> Batch:
    batch: bytes = '\n'.join([
        OpenAiBatchCompletionEntry.create_from_text_chunk(chunk_index=chunk_index, text_chunk=text_chunk).model_dump_json()
        for chunk_index, text_chunk in text_chunks.items()
    ]).encode('utf-8')
    buffer = BytesIO(batch)
    client = openai_get_client()
    file: FileObject = client.files.create(
        file=buffer,
        purpose='batch'
    )
    batch_input_file_id = file.id
    batch: Batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "description": "Open"
        }
    )
    buffer.close()
    return batch


async def get_feature_extractions_via_api(text_chunks: TextChunks) -> Dict[int, OpenAiFeatureResponse]:
    async def send_request(client: OpenAI, chunk_index: int, messages: List[Dict[str, str]], model: str = OpenAi.llm_model) -> Tuple[int, OpenAiFeatureResponse]:
        completion: ParsedChatCompletion = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=OpenAiFeatureResponse
        )
        return chunk_index, completion.choices[0].message.parsed

    prompts = [(idx, create_feature_extraction_messages(chunk)) for idx, chunk in text_chunks.items()]
    _client = openai_get_client()
    results = await asyncio.gather(*[send_request(_client, idx, msgs) for idx, msgs in prompts])
    _result_dict = dict()
    for _index, result in results:
        _result_dict[_index] = result
    return clean_all_llm_tag_choices(_result_dict)


def clean_llm_tag_choice(choices, options, distance_function, chunk_index=''):
    df = create_distance_dataframe(choices, options, distance_function)
    cleaned_list = []
    for idx, row in df.iterrows():
        sorted_row = row.sort_values(ascending=False)
        value, score = (sorted_row.index[0], sorted_row.iloc[0]) if not sorted_row.empty else (None, None)
        if score is not None and score > 0.9:
            cleaned_list.append(value)
    print(f'Matched Tags to Chunk Index {chunk_index}: {cleaned_list}')
    return cleaned_list


def clean_llm_tag_choices(feature_response: OpenAiFeatureResponse):
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


def clean_all_llm_tag_choices(feature_responses: Dict[int, OpenAiFeatureResponse]):
    for index, feature_response in feature_responses.items():
        clean_llm_tag_choices(feature_response)
    return feature_responses
