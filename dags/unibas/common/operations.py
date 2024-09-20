import asyncio
import json
from asyncio import gather as asyncio_gather
from typing import Any, Dict, List

from airflow.models import DagRun
from airflow.providers.mongo.hooks.mongo import MongoHook, MongoClient
from airflow.providers.openai.hooks.openai import OpenAIHook
from airflow.utils.state import DagRunState
from bs4 import BeautifulSoup
from bson import ObjectId
from bson.errors import InvalidId
from openai import OpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCall
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertManyResult, UpdateResult
from toolz import merge, pipe, partition_all

import unibas.common.web.mime_types as mime_types
from unibas.common.typing import SitemapQuery, WebResource, IsoTime, Batch, HtmlResource, WebClientResponse, \
    ParsedHtml, CleanedHtml, NestedIndexedTexts, IndexedTexts, Text, Index, Texts, NestedIndexedEmbeddings, \
    NestedIndexedTags, Messages, IndexedCompletion, IndexedEmbeddings, AsyncChatCompletions, \
    AsyncChatCompletion, IndexedTags, EmbeddingModel, LlmModel, TaggingFunction, OpenAiTools, Tags, HtmlAttributes, \
    HtmlDocument, NestedIndexed, FlattenedIndex, MongoHtmlBatch, MongoQuery, all_to_dict
from unibas.common.util.constants import MongoAtlas, OpenAi
from unibas.common.util.misc import vectorize, list_if_not, deep_merge, async_partition
from unibas.common.util.parsing import get_text_data_from_html, parse_html_title, parse_html_author, \
    parse_html_description, parse_html_keywords, parse_html_body, parse_html_links
from unibas.common.util.text import replace_escape_sequences_with_spaces, contract_consecutive_whitespaces, \
    split_into_sentences, collect_sentences_into_chunks
from unibas.common.web.client import fetch_resource_batch
from unibas.common.web.sitemap import query_sitemap


class TimeOps:
    @staticmethod
    def get_latest_successful_dag_run_date_or_none(dag_id: Text) -> IsoTime:
        try:
            dag_runs: List[DagRun] = DagRun.find(dag_id=dag_id)
            dag_runs.sort(key=lambda x: x.execution_date, reverse=True)
            latest_successful_dag_run: DagRun | None = None
            for dag_run in dag_runs:
                if dag_run.get_state() == DagRunState.SUCCESS:
                    latest_successful_dag_run = dag_run
                    break
            if latest_successful_dag_run is None:
                print(f'No successful dag run found, returning none and let the operator choose a start date.')
                return IsoTime(time=None)
            return IsoTime(time=latest_successful_dag_run.execution_date.isoformat())
        except Exception as e:
            raise ValueError({'Could not retrieve latest successful DagRun': str(e)})


class SitemapOps:
    @staticmethod
    def execute_sitemap_query(query: SitemapQuery) -> List[WebResource]:
        return query_sitemap(query)


class DownloadOps:
    @staticmethod
    def download_batch(batch: Batch, batch_size: int) -> List[WebClientResponse]:
        if isinstance(batch, MongoHtmlBatch):
            return fetch_resource_batch(batch.resources, batch_size)
        else:
            raise ValueError(f'No handling for mime type {batch.mime_type}')


class GlueOps:
    @staticmethod
    def batches_from_html_resources(dag_id: Text, html_resources: List[HtmlResource], batch_size: int) -> List[Batch]:
        return [
            Batch(
                dag_id=dag_id,
                mime_type=mime_types.TEXT_HTML,
                batch_size=len(partition),
                resources=all_to_dict(partition),
            ) for partition in partition_all(
                batch_size,
                html_resources
            )
        ]

    @staticmethod
    def parse_attributes_from_html_response(parsed_html: List[ParsedHtml]) -> Dict[Index, HtmlAttributes]:
        return {index: HtmlAttributes(
            loc=html.loc,
            author=html.author,
            description=html.description,
            keywords=html.keywords,
            lastmod=html.lastmod.timestamp(),
        ) for index, html in enumerate(parsed_html, start=0)}

    @staticmethod
    def flatten_nested_index(nested_index: NestedIndexed) -> FlattenedIndex:
        return [(int(k), v) for k, v in nested_index.items()]

    @staticmethod
    def create_html_documents_from_data(
            html: List[ParsedHtml],
            texts: NestedIndexedTexts,
            embeddings: NestedIndexedEmbeddings,
            tags: NestedIndexedTags
    ) -> List[HtmlDocument]:
        attributes: Dict[Index, HtmlAttributes] = GlueOps.parse_attributes_from_html_response(html)
        documents: List[HtmlDocument] = []
        data: NestedIndexed = deep_merge(texts, tags, embeddings)
        for document_index, chunks in GlueOps.flatten_nested_index(data):
            for chunk_index, chunk in GlueOps.flatten_nested_index(chunks):
                documents.append(HtmlDocument(
                    document_id=attributes[document_index].loc,
                    chunk_id=attributes[document_index].loc + '-' + str(chunk_index),
                    chunk_index=chunk_index,
                    text=chunk['text'],
                    embedding=chunk['embedding'],
                    tags=chunk['tags'],
                    attributes=attributes[document_index]
                ))
        return documents


class SplitOps:
    @staticmethod
    def split_text(text: Text) -> IndexedTexts:
        return pipe(
            text,
            split_into_sentences,
            collect_sentences_into_chunks
        )

    @staticmethod
    def split_texts(texts: Texts) -> NestedIndexedTexts:
        nested_indexed_texts: NestedIndexedTexts = dict()
        for idx in range(len(texts)):
            nested_indexed_texts[idx] = SplitOps.split_text(texts[idx])
        return nested_indexed_texts


class MongoOps:
    @staticmethod
    def _serialize_object_id(document: dict) -> dict:
        if '_id' in document and isinstance(document['_id'], ObjectId):
            document['_id'] = str(document['_id'])
        return document

    @staticmethod
    def _serialize_object_ids_in_list(documents: list) -> list:
        return [MongoOps._serialize_object_id(doc) for doc in documents]

    @staticmethod
    def _deserialize_object_id(document: dict) -> dict:
        if '_id' in document and isinstance(document['_id'], str):
            try:
                document['_id'] = ObjectId(document['_id'])
            except InvalidId:
                print(f"Invalid ObjectId string: {document['_id']}")
        return document

    @staticmethod
    def _deserialize_object_ids_in_list(documents: list) -> list:
        return [MongoOps._deserialize_object_id(doc) for doc in documents]

    @staticmethod
    def _get_mongo_client() -> MongoClient:
        return MongoHook(conn_id=MongoAtlas.conn_id).get_conn()

    @staticmethod
    def _on_collection(query: MongoQuery) -> Collection:
        return MongoOps._get_mongo_client().get_database(query.database).get_collection(query.collection)

    @staticmethod
    def mongo_insert_many(query: MongoQuery) -> InsertManyResult:
        return MongoOps._on_collection(query).insert_many(
            MongoOps._deserialize_object_ids_in_list(query.query)
        )

    @staticmethod
    def mongo_update_many(query: MongoQuery) -> UpdateResult:
        return MongoOps._on_collection(query).update_many(query.query, query.update)

    @staticmethod
    def mongo_update_one(query: MongoQuery) -> UpdateResult:
        return MongoOps._on_collection(query).update_one(
            MongoOps._deserialize_object_id(query.query),
            query.update
        )

    @staticmethod
    def mongo_delete_one(query: MongoQuery) -> DeleteResult:
        return MongoOps._on_collection(query).delete_one(
            MongoOps._deserialize_object_id(query.query)
        )

    @staticmethod
    def mongo_find(query: MongoQuery) -> List[Dict[Text, Any]]:
        return MongoOps._serialize_object_ids_in_list(
            list(MongoOps._on_collection(query).find(query.query))
        )

    @staticmethod
    def mongo_find_one(query: MongoQuery) -> Dict[Text, Any]:
        return MongoOps._serialize_object_id(
            MongoOps._on_collection(query).find_one(
                MongoOps._deserialize_object_id(query.query)
            )
        )

    @staticmethod
    def mongo_find_one_and_update(query: MongoQuery) -> Dict[Text, Any]:
        return MongoOps._serialize_object_id(
            MongoOps._on_collection(query).find_one_and_update(
                MongoOps._deserialize_object_id(query.query),
                query.update
            )
        )

    @staticmethod
    def mongo_find_one_and_delete(query: MongoQuery) -> Dict[Text, Any]:
        return MongoOps._serialize_object_id(
            MongoOps._on_collection(query).find_one_and_delete(
                MongoOps._deserialize_object_id(query.query)
            )
        )

    @staticmethod
    def mongo_delete_many(query: MongoQuery) -> DeleteResult:
        return MongoOps._on_collection(query).delete_many(query.query)


class CleanOps:
    @staticmethod
    def clean_html_text(parsed_html_response: ParsedHtml) -> CleanedHtml:
        return CleanedHtml(**merge(parsed_html_response.dict(), {'content': pipe(
            parsed_html_response.content,
            get_text_data_from_html,
            replace_escape_sequences_with_spaces,
            contract_consecutive_whitespaces
        )}))

    @staticmethod
    def clean_html_texts(parsed_html_responses: List[ParsedHtml]) -> List[CleanedHtml]:
        return vectorize(CleanOps.clean_html_text)(parsed_html_responses)


class ParseOps:
    @staticmethod
    def parse_html_response(web_client_response: WebClientResponse) -> ParsedHtml:
        soup = BeautifulSoup(web_client_response.content, 'html.parser')
        return ParsedHtml(**merge(web_client_response.dict(), {
            'title': parse_html_title(soup),
            'author': parse_html_author(soup),
            'description': parse_html_description(soup),
            'keywords': parse_html_keywords(soup),
            'content': parse_html_body(soup),
            'links': parse_html_links(web_client_response.loc, soup),
        }))

    @staticmethod
    def parse_html_responses(web_client_responses: List[WebClientResponse]) -> List[ParsedHtml]:
        return vectorize(ParseOps.parse_html_response)(web_client_responses)


class OpenAiOps:
    @staticmethod
    def openai_get_client() -> OpenAI:
        hook = OpenAIHook(conn_id=OpenAi.conn_id)
        return hook.get_conn()

    @staticmethod
    def get_embeddings_response_from_texts(
            client: OpenAI,
            embedding_model: EmbeddingModel,
            texts: Texts
    ) -> CreateEmbeddingResponse:
        print(f'Sending OpenAI embedding request model={embedding_model} texts={texts}')
        return client.embeddings.create(
            input=texts,
            model=embedding_model,
        )

    @staticmethod
    def get_indexed_embeddings_from_texts(
            client: OpenAI,
            embeddings_model: EmbeddingModel,
            texts: Texts
    ) -> IndexedEmbeddings:
        response = OpenAiOps.get_embeddings_response_from_texts(client, embeddings_model, texts)
        embeddings = {
            k: v for k, v in [
                (e.index, e.embedding) for e in response.data
            ]
        }
        print(f'Received OpenAI response from embedding request model={embeddings_model} #embeddings={len(embeddings)} embeddings={[str(embeddings[0]) + "...[...]"]}')
        return embeddings

    @staticmethod
    def get_indexed_embeddings_from_indexed_texts(
            client: OpenAI,
            embeddings_model: EmbeddingModel,
            texts: IndexedTexts
    ) -> IndexedEmbeddings:
        return OpenAiOps.get_indexed_embeddings_from_texts(
            client,
            embeddings_model,
            [text for _, text in texts.items()]
        )

    @staticmethod
    def get_nested_indexed_embeddings_from_nested_indexed_texts(
            client: OpenAI,
            embeddings_model: EmbeddingModel,
            texts: NestedIndexedTexts
    ) -> NestedIndexedEmbeddings:
        return {
            k: OpenAiOps.get_indexed_embeddings_from_indexed_texts(
                client,
                embeddings_model,
                indexed_texts
            ) for k, indexed_texts in texts.items()
        }

    @staticmethod
    def create_messages_from_texts_and_instructions(messages: Text | Texts, instructions: Text) -> Messages:
        msg = [{'role': 'system', 'content': instructions}] if instructions is not None else []
        msg.extend([{'role': 'user', 'content': m} for m in list_if_not(messages)])
        return msg

    @staticmethod
    async def get_async_chat_completion(
            client: OpenAI,
            model: Text,
            index: Index,
            texts: Text | Texts,
            instructions: Text = None,
            tools: OpenAiTools = None
    ) -> AsyncChatCompletion:
        print(f'Sending OpenAI completion request to openai model={model} texts={list_if_not(texts)[0]}... tools={len(tools)}')
        return AsyncChatCompletion(index=index, completion=client.chat.completions.create(
            model=model,
            messages=OpenAiOps.create_messages_from_texts_and_instructions(texts, instructions),
            tools=tools,
            tool_choice='none' if not tools else 'required',
        ))

    @staticmethod
    async def get_async_chat_completions(
            client: OpenAI,
            model: Text,
            messages: IndexedTexts,
            instructions: Text = None,
            tools: OpenAiTools = None,
            batch_size=10
    ) -> AsyncChatCompletions:
        async for message in async_partition(messages.items(), batch_size):
            yield await asyncio_gather(
                *[OpenAiOps.get_async_chat_completion(
                    client,
                    model,
                    index,
                    m,
                    instructions,
                    tools
                ) for index, m in message]
            )

    @staticmethod
    def get_batch_completion(
            client: OpenAI,
            model: LlmModel,
            messages: IndexedTexts,
            instructions: Text = None,
            tools: OpenAiTools = None,
            batch_size=10
    ) -> IndexedCompletion:
        async def execute():
            completions = dict()
            async for batch in OpenAiOps.get_async_chat_completions(
                    client,
                    model,
                    messages,
                    instructions,
                    tools,
                    batch_size
            ):
                for async_chat_completion in batch:
                    print(f'Received OpenAI completion response for index={async_chat_completion.index}')
                    completions[async_chat_completion.index] = async_chat_completion.completion
            return completions

        return asyncio.run(execute())

    @staticmethod
    def parse_tagging_completion_tool_call(completion: ChatCompletion) -> Tags:
        tool_call: ChatCompletionMessageToolCall = completion.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        tags = arguments.get('tags', [])
        return tags

    @staticmethod
    def get_indexed_tags_from_indexed_texts(
            client: OpenAI,
            model: LlmModel,
            messages: IndexedTexts,
            instructions: Text,
            tagging_function: TaggingFunction,
            batch_size=10
    ) -> IndexedTags:
        completions = OpenAiOps.get_batch_completion(
            client,
            model,
            messages,
            instructions,
            [tagging_function],
            batch_size=batch_size
        )
        return {
            k: OpenAiOps.parse_tagging_completion_tool_call(v)
            for k, v in completions.items()
        }

    @staticmethod
    def get_nested_indexed_tags_from_nested_indexed_texts(
            client: OpenAI,
            model: LlmModel,
            messages: NestedIndexedTexts,
            instructions: Text,
            tagging_function: TaggingFunction,
            batch_size=10
    ) -> NestedIndexedTags:
        return {
            k: OpenAiOps.get_indexed_tags_from_indexed_texts(
                client,
                model,
                m,
                instructions,
                tagging_function,
                batch_size=batch_size
            ) for k, m in messages.items()
        }

    @staticmethod
    def create_tags(
            nested_indexed_texts: NestedIndexedTexts,
            tagging_function: TaggingFunction,
            instructions: Text,
    ) -> NestedIndexedTags:
        return OpenAiOps.get_nested_indexed_tags_from_nested_indexed_texts(
            OpenAiOps.openai_get_client(),
            OpenAi.llm_model,
            nested_indexed_texts,
            instructions,
            tagging_function
        )

    @staticmethod
    def openai_embeddings_from_nested_indexed_text(
            nested_indexed_texts: NestedIndexedTexts
    ) -> NestedIndexedEmbeddings:
        return OpenAiOps.get_nested_indexed_embeddings_from_nested_indexed_texts(
            OpenAiOps.openai_get_client(),
            OpenAi.embedding_model,
            nested_indexed_texts
        )