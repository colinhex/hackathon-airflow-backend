import asyncio
from io import BytesIO

from airflow.providers.openai.hooks.openai import OpenAIHook
from openai import OpenAI
from openai.types import CreateEmbeddingResponse, FileObject, Batch
from openai.types.chat import ParsedChatCompletion
from typing_extensions import List, Dict, Tuple, Literal, Callable

from unibas.common.environment import OpenAiEnvVariables, TestEnvVariables
from unibas.common.logic.math_logic import create_distance_dataframe, sequence_matcher_distance
from unibas.common.model.oai_model import OpenAiEmbeddings, OpenAiFeatureResponse, OpenAiBatchCompletionEntries
from unibas.common.model.parsed_model import TextChunks
from unibas.common.model.prompt_model import create_feature_extraction_messages, FACULTIES, INTENDED_AUDIENCE, \
    DEPARTMENTS, ADMINISTRATIVE_SERVICES, DEGREE_LEVELS, TOPICS, INFORMATION_TYPE


def openai_get_client() -> OpenAI:
    test_api_key = TestEnvVariables.open_ai_api_key
    if test_api_key is not None:
        return OpenAI(api_key=test_api_key)
    return OpenAIHook(conn_id=OpenAiEnvVariables.conn_id).get_conn()


def get_embeddings(client: OpenAI, embeddings: OpenAiEmbeddings) -> OpenAiEmbeddings:
    print(f'Outgoing Request: Sending embedding request to OpenAI API for chunks: {embeddings.embeddings.keys()}')
    response: CreateEmbeddingResponse = client.embeddings.create(
        input=embeddings.get_ordered_text_chunks(),
        model=embeddings.embedding_model,
    )
    print(f'Incoming Response: Received embeddings for chunks: {embeddings.embeddings.keys()}')
    return collect_embeddings(embeddings, response)


def get_embeddings_from_text_chunks(client: OpenAI, text_chunks: TextChunks, embedding_model=OpenAiEnvVariables.embedding_model) -> OpenAiEmbeddings:
    return get_embeddings(client, embeddings_query_from_text_chunks(text_chunks=text_chunks, embedding_model=embedding_model))


def collect_embeddings(embeddings: OpenAiEmbeddings, response: CreateEmbeddingResponse) -> OpenAiEmbeddings:
    for _response in response.data:
        embeddings.add_embedding(chunk_index=_response.index, embedding=_response.embedding)
    print(f'Collected response embeddings.')
    return embeddings


def embeddings_query_from_text_chunks(text_chunks: TextChunks, embedding_model: str = OpenAiEnvVariables.embedding_model) -> OpenAiEmbeddings:
    embeddings = OpenAiEmbeddings(embedding_model=embedding_model)
    for chunk_index, text_chunk in text_chunks.items():
        embeddings.add_text_chunk(chunk_index=chunk_index, text_chunk=text_chunk)
    print('Created embeddings query.')
    return embeddings


def create_batch_input_file(text_chunks: TextChunks, message_generator) -> bytes:
    batch_completion_entries = OpenAiBatchCompletionEntries()
    for chunk_index, text_chunk in text_chunks.items():
        batch_completion_entries.add(chunk_index, text_chunk, message_generator)

    batch_input_file: str = batch_completion_entries.to_batch_file_str()
    print(f'Created batch completion file:\n{batch_input_file}')
    return batch_input_file.encode('utf-8')


def create_file(client: OpenAI, file: bytes, purpose: Literal["assistants", "batch", "fine-tune", "vision"]) -> FileObject:
    buffer = BytesIO(file)
    file: FileObject = client.files.create(
        file=buffer,
        purpose=purpose
    )
    buffer.close()
    return file


def create_batch(
        client: OpenAI,
        file: FileObject,
        endpoint: Literal["/v1/chat/completions", "/v1/embeddings", "/v1/completions"] = '/v1/chat/completions',
        batch_description: str = 'OpenAI Batch Completions',
) -> Batch:
    return client.batches.create(
        input_file_id=file.id,
        endpoint=endpoint,
        completion_window="24h",
        metadata={
            "description": batch_description
        }
    )


def get_feature_extractions_via_batch_api(
        client: OpenAI,
        text_chunks: TextChunks,
        message_generator: Callable[[TextChunks], List[Dict[str, str]]] = create_feature_extraction_messages
) -> Tuple[FileObject, Batch]:
    print('Called on to create batch request for openai for text chunks: ', text_chunks)
    file: FileObject = client.files.create(file=create_batch_input_file(text_chunks, message_generator), purpose='batch')
    batch: Batch = create_batch(client, file)
    return file, batch


async def get_feature_extractions_via_api(client: OpenAI, text_chunks: TextChunks) -> Dict[int, OpenAiFeatureResponse]:
    async def send_request(_client: OpenAI, chunk_index: int, messages: List[Dict[str, str]], model: str = OpenAiEnvVariables.llm_model) -> Tuple[int, OpenAiFeatureResponse]:
        print(f'Outgoing Request: Sending request for chunk index {chunk_index}')
        completion: ParsedChatCompletion = _client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=OpenAiFeatureResponse
        )
        print(f'Incoming Response: Received response for chunk index {chunk_index}')
        return chunk_index, completion.choices[0].message.parsed

    print('Creating prompts for feature extraction')
    prompts = [(idx, create_feature_extraction_messages(chunk)) for idx, chunk in text_chunks.items()]
    print('Sending requests to OpenAI API')
    results = await asyncio.gather(*[send_request(client, idx, msgs) for idx, msgs in prompts])
    print('Processing responses from OpenAI API')
    result_dict = {index: result for index, result in results}
    return clean_all_llm_tag_choices(result_dict)


def clean_llm_tag_choice(choices, options, distance_function):
    df = create_distance_dataframe(choices, options, distance_function)
    cleaned_list = []

    for idx, row in df.iterrows():
        sorted_row = row.sort_values(ascending=False)
        value, score = (sorted_row.index[0], sorted_row.iloc[0]) if not sorted_row.empty else (None, None)
        if score is not None and score > 0.9:
            cleaned_list.append(value)

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
