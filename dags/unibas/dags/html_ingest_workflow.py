""""
from datetime import datetime, timedelta

from airflow import XComArg
from airflow.decorators import dag, task
from airflow.providers.mongo.sensors.mongo import MongoSensor
from toolz import unique

from unibas.common.operations import *
from unibas.common.typing import NestedIndexedEmbeddings, MongoHtmlBatch, all_to_dict


def on_failure_callback(context):
    print(f"Task {context['task_instance_key_str']} failed.")


@dag(
    dag_display_name="HTML Ingest Workflow",
    dag_id="html_ingest_workflow",
    schedule_interval=None,  # Adjust schedule as needed
    start_date=datetime(2022, 10, 28),
    catchup=False,
    tags=["webscraping"],
    default_args={
        "owner": "unibas",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        'on_failure_callback': on_failure_callback
    }
)
def html_ingest_workflow():

    mongo_sensor = MongoSensor(
        task_id='check_for_new_html_batch',
        mongo_conn_id=MongoAtlas.conn_id,
        mongo_db=MongoAtlas.airflow_database,
        collection=MongoAtlas.batch_collection,
        query={
            'mime_type': 'text/html',
            'tries': {
                '$lt': 3
            },
            # 'processing': False
        },
        mode='poke',
        poke_interval=60,
        do_xcom_push=True
    )

    @task
    def get_batch_data(_sensor):
        return MongoHtmlBatch(**MongoOps.mongo_find_one_and_update(MongoQuery(
            database=MongoAtlas.airflow_database,
            collection=MongoAtlas.batch_collection,
            query={
                'mime_type': 'text/html',
                'tries': {
                    '$lt': 3
                },
                # 'processing': False
            },
            update={
                '$inc': {'tries': 1},
                '$set': {'processing': True}
            }
        ))).dict()

    @task
    def download_html_data(html_batch):
        return all_to_dict(DownloadOps.download_batch(MongoHtmlBatch(**html_batch), batch_size=25))

    @task
    def parse_html_data(html_responses):
        return all_to_dict(ParseOps.parse_html_responses(WebClientResponse.from_serialised_list(html_responses)))

    @task
    def clean_html_data(parsed_html_data):
        return all_to_dict(CleanOps.clean_html_texts(ParsedHtml.from_serialised_list(parsed_html_data)))

    @task
    def split_html_text_data(cleaned_html_data):
        return {
            'data': SplitOps.split_texts([clean_html.content for clean_html in CleanedHtml.from_serialised_list(cleaned_html_data)])
        }

    @task
    def create_html_embeddings(texts):
        return {
            'data': OpenAiOps.openai_embeddings_from_nested_indexed_text(texts['data'])
        }

    @task
    def generate_html_tags(texts):
        return {'data': OpenAiOps.create_tags(
            texts['data'],
            instructions="Tag the following content based on its themes. Multiple tags are possible.",
            tagging_function={
                "type": "function",
                "function": {
                    "name": "tag_content",
                    "strict": True,
                    "description": "Categorizes the content with predefined tags that match its themes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "students",
                                        "researchers",
                                        "faculty",
                                        "administrators",
                                    ]
                                }
                            },
                        },
                        "required": ["tags"],
                        "additionalProperties": False,
                    }
                }
            }
        )}

    @task
    def create_html_documents(
            parsed_html_data,
            texts,
            embeddings,
            tags
    ):
        return all_to_dict(GlueOps.create_html_documents_from_data(
            ParsedHtml.from_serialised_list(parsed_html_data),
            texts['data'],
            embeddings['data'],
            tags['data']
        ))

    @task
    def clear_html_documents(batch) -> int:
        doc_ids: List[Text] = list(unique([doc.document_id for doc in HtmlDocument.from_serialised_list(batch)]))

        delete_result: DeleteResult = MongoOps.mongo_delete_many(MongoQuery(
            database=MongoAtlas.vector_database,
            collection=MongoAtlas.embeddings_collection,
            query={
                'document_id': {
                    '$in': doc_ids
                }
            }
        ))
        print(f'Deleted {delete_result.deleted_count} documents:\n{delete_result.__str__()}')
        return delete_result.deleted_count

    @task
    def ingest_html_documents(cleared: int, created) -> int:
        print(f'Called to ingest {len(created)} documents, cleared {cleared} documents.')
        MongoOps.mongo_insert_many(MongoQuery(
            database=MongoAtlas.vector_database,
            collection=MongoAtlas.embeddings_collection,
            query=created
        ))
        print(f'Ingested {len(created)} documents.')
        return len(created)

    @task
    def delete_html_batch(ingested: int, _batch):
        batch: MongoHtmlBatch = MongoHtmlBatch.from_serialised(_batch)
        print(f'Successfully ingested {ingested} documents.')
        print(f'Deleting batch {batch.get_object_id()}')
        MongoOps.mongo_delete_one(MongoQuery(
            database=MongoAtlas.airflow_database,
            collection=MongoAtlas.batch_collection,
            query={
                '_id': batch.get_object_id()
            }
        ))

    sensor: XComArg = mongo_sensor.output
    mongo_html_batch = get_batch_data(sensor)

    web_client_responses = download_html_data(mongo_html_batch)
    parsed_html_responses = parse_html_data(web_client_responses)
    cleaned_html_responses = clean_html_data(parsed_html_responses)

    nested_indexed_texts = split_html_text_data(cleaned_html_responses)
    nested_indexed_embeddings = create_html_embeddings(nested_indexed_texts)
    nested_indexed_tags = generate_html_tags(nested_indexed_texts)

    created_html_documents = create_html_documents(
        parsed_html_data=parsed_html_responses,
        texts=nested_indexed_texts,
        tags=nested_indexed_tags,
        embeddings=nested_indexed_embeddings
    )

    number_of_cleared_documents: int = clear_html_documents(created_html_documents)
    number_of_ingested_documents: int = ingest_html_documents(number_of_cleared_documents, created_html_documents)

    delete_html_batch(number_of_ingested_documents, mongo_html_batch)


# Instantiate the DAG
ingest_workflow_dag_instance = html_ingest_workflow()


"""
