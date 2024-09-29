from typing import List

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.results import UpdateResult, InsertManyResult, DeleteResult
from toolz import unique
from typing_extensions import Dict

from unibas.common.logic.logic_mongo import *
from unibas.common.logic.logic_oai import create_embeddings, create_feature_extractions
from unibas.common.logic.logic_parse import parse
from unibas.common.logic.logic_web_client import fetch_resource_batch
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_job import Job, DocumentChunk
from unibas.common.model.model_parsed import ParsedWebContentTextChunks, ParsedWebContentHtml, ParsedWebContentPdf, \
    UrlParseResult, UrlGraph
from unibas.common.model.model_utils import dump_all_models


def get_job() -> Job:
    job = on_batch_collection().find_one_and_update(
        {
            # Get a job that is not processing and has been tried less than 3 times
            'tries': {
                '$lt': 3
            },
            'processing': False
        },
        {
            # Increment the tries by 1 and set processing to True
            '$inc': {
                'tries': 1
            },
            '$set': {
                'processing': True
            }
        },
        return_document=ReturnDocument.AFTER
    )
    if job is None:
        raise ValueError('No job found.')
    return Job.parse_obj(job)


def get_job_by_id(job_id: ObjectId) -> Job:
    print('Querying mongo for job data.')

    job = on_batch_collection().find_one(
        {
            '_id': job_id
        }
    )

    if job is None:
        raise ValueError(f'Job with id {job_id} not found.')
    return Job.parse_obj(job)


def update_job(job: Job):
    print('Updating job data.')

    update_result: UpdateResult = on_batch_collection().update_one(
        {
            '_id': job.id
        },
        {
            '$set': job.model_dump(by_alias=True)
        }
    )

    if not update_result.acknowledged:
        raise ValueError('Failed to update job data.')


def check_for_document_chunks(job: Job) -> bool:
    for resource in job.resources:
        if isinstance(resource, DocumentChunk):
            return True
    return False


def verify_resources_available(job: Job):
    # Check if resources are available
    if job.resources is None or len(job.resources) == 0:
        raise ValueError(f'No resources found in the job. Defunct monitor? monitor={job.created_by}')


def download_resources(job: Job):
    job.resources = fetch_resource_batch(job.resources)


def verify_download_success(job: Job):
    # Check for download failures
    for resource in job.resources:
        if not HttpCode.success(resource.code):
            raise ValueError(f'Failed to download resource: {resource.loc}')


def parse_resources(job: Job):
    job.resources = [parse(resource) for resource in job.resources]


def collect_links_into_graph_and_remove_from_attributes(job: Job) -> UrlGraph:
    url_parse_results = []
    for resource in job.resources:
        if isinstance(resource, ParsedWebContentHtml):
            print(f'Collecting links from resource: {resource.loc}')
            url_parse_results.append(resource.attributes.links)
            print(f'Removing links from attributes: {resource.loc}')
            resource.attributes.links = UrlParseResult(origin=resource.loc)
    if len(url_parse_results) == 0:
        print('No links to collect.')
        return UrlGraph()
    return UrlGraph.merge_all([links.get_graph_data() for links in url_parse_results])


def verify_text_chunks_available(job: Job):
    # Check that text chunks are available
    for resource in job.resources:
        if not isinstance(resource, ParsedWebContentTextChunks):
            raise ValueError(f'Invalid resource type: {resource.loc}')


def create_embeddings_for_job(job: Job) -> Dict[str, List[List[float]]]:
    return create_embeddings(job)


def verify_embeddings_available(job: Job, embeddings: Dict[str, List[List[float]]]):
    for resource in job.resources:
        assert isinstance(resource, ParsedWebContentTextChunks)
        if str(resource.id) not in embeddings:
            raise ValueError(f'No embeddings found for resource: {resource.loc}')
        if len(embeddings[str(resource.id)]) != len(resource.content):
            raise ValueError(f'Invalid number of embeddings for resource: {resource.loc}')


def extract_features_for_job(job: Job):
    return create_feature_extractions(job)


def verify_feature_extraction_available(job: Job, features: Dict[str, List[Dict[str, str]]]):
     for resource in job.resources:
        assert isinstance(resource, ParsedWebContentTextChunks)
        if str(resource.id) not in features:
            raise ValueError(f'No features found for resource: {resource.loc}')
        if len(features[str(resource.id)]) != len(resource.content):
            raise ValueError(f'Invalid number of features for resource: {resource.loc}')


def create_chunk_document_from_job(job: Job):
    chunk_documents = []
    for resource in job.resources:
        chunk_documents.extend(create_documents_for_resource(resource))
    job.resources = chunk_documents


def create_documents_for_resource(resource):
    assert (isinstance(resource, ParsedWebContentHtml)
            or isinstance(resource, ParsedWebContentPdf))

    chunk_documents = []

    metadata = dict()
    metadata['document_id'] = str(resource.loc)
    metadata['attributes'] = resource.attributes
    metadata['lastmod'] = resource.lastmod

    for index, chunk in enumerate(resource.content):
        chunk_metadata = metadata.copy()
        chunk_metadata['chunk_id'] = str(resource.loc) + '_' + str(index)
        chunk_metadata['chunk_index'] = index

        chunk_document = dict()
        chunk_document['text'] = chunk
        chunk_document['embedding'] = resource.embeddings[index]
        chunk_document['tags'] = resource.features[index]
        chunk_document['metadata'] = chunk_metadata

        chunk_documents.append(DocumentChunk(**chunk_document))

    return chunk_documents


def delete_old_documents_from_vector_embeddings_collection(job: Job):
    document_ids = list(unique([resource.metadata.document_id for resource in job.resources]))
    print(f'Deleting old documents:')
    for document_id in document_ids:
        print(f'\t- metadata.document_id={document_id}')

    delete_result: DeleteResult = on_embedding_collection().delete_many(
        {
            'metadata.document_id': {
                '$in': document_ids
            }
        }
    )

    if not delete_result.acknowledged:
        raise ValueError('Failed to delete documents.')
    print(f'Deleted existing document chunks: {delete_result.deleted_count}')


def upload_new_documents_to_vector_embeddings_collection(job: Job):
    document_ids = list(unique([resource.metadata.document_id for resource in job.resources]))
    print(f'Inserting new documents:')
    for document_id in document_ids:
        print(f'\t- metadata.document_id={document_id}')

    insert_result: InsertManyResult = on_embedding_collection().insert_many(
        dump_all_models(job.resources)
    )

    if not insert_result.acknowledged:
        raise ValueError('Failed to insert documents.')
    print(f'Inserted new document chunks:')
    for insertion_id in insert_result.inserted_ids:
        print(f'\t- _id={str(insertion_id)}')


def verify_documents_available(job: Job):
    for resource in job.resources:
        assert isinstance(resource, DocumentChunk)


def on_job_failure(job_id: str):
    print(f'Job failed: {job_id}, setting processing to False.')

    on_batch_collection().update_one(
        {
            '_id': ObjectId(job_id)
        },
        {
            '$set': {
                'processing': False
            }
        }
    )


def on_job_success(job_id: str):
    print(f'Job succeeded: {job_id}, deleting job data.')

    on_batch_collection().delete_one(
        {
            '_id': ObjectId(job_id)
        }
    )