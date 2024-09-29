import asyncio
from io import BytesIO

from airflow.providers.openai.hooks.openai import OpenAIHook
from openai import OpenAI
from openai.types import CreateEmbeddingResponse, FileObject, Batch
from openai.types.chat import ParsedChatCompletion
from typing_extensions import List, Tuple, Literal, Callable

from unibas.common.logic.logic_math import create_distance_dataframe, sequence_matcher_distance
from unibas.common.model.model_annotations import Indexed
from unibas.common.model.model_openai import *
from unibas.common.model.model_prompt import *


def openai_get_client(open_ai_key=None) -> OpenAI:
    if open_ai_key is not None:
        return OpenAI(api_key=open_ai_key)
    if OpenAiEnvVariables.test_api_key is not None:
        return OpenAI(api_key=OpenAiEnvVariables.test_api_key)
    return OpenAIHook(conn_id=OpenAiEnvVariables.conn_id).get_conn()


def create_embeddings(job: Job) -> Dict[str, List[List[float]]]:
    embeddings = OpenAiEmbeddings()
    embeddings.add_job(job)
    get_embeddings(openai_get_client(), embeddings)
    return {
        str(resource.id): embeddings.get_ordered_embeddings(str(resource.id))
        for resource in job.resources
    }


def get_embeddings(client: OpenAI, embeddings: OpenAiEmbeddings) -> OpenAiEmbeddings:
    print(f'Outgoing Request: Sending embedding request to OpenAI API for chunks: {len(embeddings.embeddings)}')
    response: CreateEmbeddingResponse = client.embeddings.create(
        input=embeddings.get_ordered_text_chunks(),
        model=embeddings.embedding_model
    )
    print(f'Incoming Response: Received embeddings for chunks: {len(embeddings.embeddings)}')
    return collect_embeddings(embeddings, response)


def get_embeddings_from_text_chunks(client: OpenAI, resource_id, text_chunks: Indexed, embedding_model=OpenAiEnvVariables.embedding_model) -> OpenAiEmbeddings:
    return get_embeddings(client, embeddings_query_from_text_chunks(resource_id, text_chunks=text_chunks, embedding_model=embedding_model))


def collect_embeddings(embeddings: OpenAiEmbeddings, response: CreateEmbeddingResponse) -> OpenAiEmbeddings:

    for _response in response.data:
        embeddings.add_embedding(embedding_index=_response.index, embedding=_response.embedding)
    print(f'Collected response embeddings.')
    return embeddings


def embeddings_query_from_text_chunks(resource_id, text_chunks: Indexed, embedding_model: str = OpenAiEnvVariables.embedding_model) -> OpenAiEmbeddings:

    embeddings = OpenAiEmbeddings(embedding_model=embedding_model)
    for chunk_index, text_chunk in text_chunks.items():
        embeddings.add_request(resource_id, chunk_index=chunk_index, text_chunk=text_chunk)
    print('Created embeddings query.')
    return embeddings


def create_batch_input_file(text_chunks: Indexed, message_generator) -> bytes:
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
    """
    Not used yet. Stub.
    """
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
        text_chunks: Indexed,
        message_generator: Callable[[Indexed], List[Dict[str, str]]] = create_feature_extraction_messages
) -> Tuple[FileObject, Batch]:
    """
    Not used yet. Stub.
    """
    print('Called on to create batch request for openai for text chunks: ', text_chunks)
    file: FileObject = client.files.create(file=create_batch_input_file(text_chunks, message_generator), purpose='batch')
    batch: Batch = create_batch(client, file)
    return file, batch


def create_feature_extractions(job: Job) -> Dict[str, List[OpenAiFeatureResponse]]:
    features = OpenAiFeatures()
    features.add_job(job)
    asyncio.run(get_feature_extractions_via_api(openai_get_client(), features))
    return {
        str(resource.id): features.get_ordered_features(str(resource.id))
        for resource in job.resources
    }


async def get_feature_extractions_via_api(client: OpenAI, features: OpenAiFeatures):
    """
    Makes feature completion requests to OpenAI for each text chunk.

    See also: create_feature_extraction_messages
    """
    async def send_request(_client: OpenAI, feature: OpenAiFeature):
        if feature.feature is not None:
            print(f'Feature already exists, skipping request for document {feature.resource_id} chunk index {feature.chunk_index}')
            return
        print(f'Outgoing Request: Sending request for document {feature.resource_id} chunk index {feature.chunk_index}')
        parsed_completion: ParsedChatCompletion = await asyncio.to_thread(
            _client.beta.chat.completions.parse,
            model=features.llm_model,
            messages=create_feature_extraction_messages(feature.text_chunk),
            response_format=OpenAiFeatureResponse
        )
        print(f'Incoming Response: Received response for document {feature.resource_id} chunk index {feature.chunk_index}')
        print('Feature:', feature.feature)
        feature.feature = clean_llm_tag_choices(OpenAiFeatureResponse.parse_raw(parsed_completion.choices[0].message.content))
        print(f'Model {features.llm_model} chose for {feature.resource_id}, chunk index {feature.chunk_index} features:', feature.feature.model_dump_json(exclude_defaults=True))

    await asyncio.gather(*[send_request(client, feature) for feature in features.features])


def clean_llm_tag_choice(choices, options, distance_function):
    """
    Clean the LLM tag choices by selecting the best match based on a distance function.

    Args:
        choices (List[str]): The list of choices to clean.
        options (List[str]): The list of options to match against.
        distance_function (Callable): The function to calculate the distance between choices and options.

    Returns:
        List[str]: The cleaned list of choices.
    """
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
