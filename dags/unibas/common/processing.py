from bson import ObjectId
from pymongo.results import UpdateResult, InsertManyResult, DeleteResult
from toolz import unique

from unibas.common.logic.logic_mongo import *
from unibas.common.model.model_job import Job, DocumentChunk
from unibas.common.model.model_mongo import MongoModel
from unibas.common.model.model_parsed import ParsedHtml, ParsedPdf, \
    UrlParseResult, UrlGraph


def get_job_by_id(job_id: ObjectId) -> Job:
    print('Querying mongo for job data.')

    job = on_job_collection().find_one(
        {
            '_id': job_id
        }
    )

    if job is None:
        raise ValueError(f'Job with id {job_id} not found.')
    return Job.parse_obj(job)


def update_job(job: Job):
    print('Updating job data.')

    update_result: UpdateResult = on_job_collection().update_one(
        {
            '_id': job.id
        },
        {
            '$set': job.model_dump(by_alias=True)
        }
    )

    if not update_result.acknowledged:
        raise ValueError('Failed to update job data.')
    return str(job.id)


def get_url_graph(name: str) -> UrlGraph:
    url_graph = on_url_graph_collection().find_one(
        {
            'name': name
        }
    )
    if url_graph is None:
        return UrlGraph(name=name)
    return UrlGraph.parse_obj(url_graph)


def update_url_graph(job: Job) -> None:
    url_parse_results = []
    for resource in job.resources:
        if isinstance(resource, ParsedHtml):
            print(f'Collecting links from resource: {resource.loc}')
            url_parse_results.append(resource.attributes.links)
            print(f'Removing links from attributes: {resource.loc}')
            resource.attributes.links = UrlParseResult(origin=resource.loc)
    if len(url_parse_results) == 0:
        print('No links to collect.')
        return

    url_graph = get_url_graph(name=job.created_by)
    for links in url_parse_results:
        url_graph.merge(links.get_graph_data(graph_name=job.created_by))

    response = on_url_graph_collection().replace_one(
        {
            'name': job.created_by
        },
        url_graph.model_dump(by_alias=True),
        upsert=True
    )

    if not response.acknowledged:
        raise ValueError('Failed to update url graph.')


def create_documents_for_resource(resource):
    assert (isinstance(resource, ParsedHtml)
            or isinstance(resource, ParsedPdf))

    chunk_documents = []

    metadata = dict()
    metadata['document_id'] = str(resource.loc)
    if isinstance(resource, ParsedHtml):
        metadata['attributes'] = resource.attributes.model_dump(exclude_none=True, exclude={'links'})
    else:
        metadata['attributes'] = resource.attributes.model_dump(exclude_none=True)

    metadata['lastmod'] = resource.lastmod

    for index, chunk in enumerate(resource.content):
        chunk_metadata = metadata.copy()
        chunk_metadata['chunk_id'] = str(resource.loc) + '_' + str(index)
        chunk_metadata['chunk_index'] = index

        chunk_document = dict()
        chunk_document['text'] = chunk
        chunk_document['embedding'] = resource.embeddings[index]
        chunk_document['tags'] = {k: v for k, v in resource.features[index].items() if len(v) > 0}
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
    return str(job.id)


def upload_new_documents_to_vector_embeddings_collection(job: Job):
    document_ids = list(unique([resource.metadata.document_id for resource in job.resources]))
    print(f'Inserting new documents:')
    for document_id in document_ids:
        print(f'\t- metadata.document_id={document_id}')

    insert_result: InsertManyResult = on_embedding_collection().insert_many(
        MongoModel.dump_all_models(job.resources)
    )

    if not insert_result.acknowledged:
        raise ValueError('Failed to insert documents.')
    print(f'Inserted new document chunks:')
    for insertion_id in insert_result.inserted_ids:
        print(f'\t- _id={str(insertion_id)}')
    return str(job.id)


def on_job_failure(job_id: str):
    print(f'Job failed: {job_id}, setting processing to False.')

    on_job_collection().update_one(
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

    on_job_collection().delete_one(
        {
            '_id': ObjectId(job_id)
        }
    )