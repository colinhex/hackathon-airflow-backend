from datetime import datetime, timedelta

from airflow.decorators import task
from airflow.models.dag import dag
from airflow.providers.mongo.sensors.mongo import MongoSensor
from typing_extensions import List

from unibas.common.environment.variables import MongoAtlasEnvVariables
from unibas.common.logic.logic_mongo import mongo_find_one_and_update
from unibas.common.logic.logic_parse import parse
from unibas.common.logic.logic_web_client import fetch_resource_batch
from unibas.common.model.model_job import Job
from unibas.common.model.model_mongo import MongoQuery, FindOneResult
from unibas.common.model.model_parsed import ParsedContentUnion
from unibas.common.model.model_resource import WebResource, WebContent


def on_failure_callback(**context):
    print(f"Task {context['task_instance_key_str']} failed.")


@dag(
    dag_display_name="XJOB Ingest",
    dag_id="xjob_ingest",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["job_sensor", "ingest_workflow"],
    default_args={
        "owner": "unibas",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        'on_failure_callback': on_failure_callback
    },
)
def x_job_ingest():
    mongo_sensor = MongoSensor(
        task_id="mongo_sensor",
        mongo_conn_id=MongoAtlasEnvVariables.conn_id,
        mongo_db=MongoAtlasEnvVariables.airflow_database,
        collection=MongoAtlasEnvVariables.batch_collection,
        query={
            'tries': {
                '$lt': 3
            },
            'processing': False
        },
        poke_interval=30,
        timeout=600,
        mode="poke",
    )

    @task.short_circuit
    def get_job_data(sensor):
        print('Querying mongo for job data.')
        job: FindOneResult = mongo_find_one_and_update(MongoQuery(
            database=MongoAtlasEnvVariables.airflow_database,
            collection=MongoAtlasEnvVariables.batch_collection,
            query={
                'tries': {
                    '$lt': 3
                },
                'processing': False
            },
            update={
                '$inc': {
                    'tries': 1
                },
                '$set': {
                    'processing': True
                }
            }
        ))
        if job is None:
            print("No job found.")
            return None
        return Job.parse_obj(job).model_dump(
            stringify_datetime=True,
            stringify_object_id=True
        )

    @task
    def process_job(job_data):
        if job_data is None:
            raise ValueError("No job data found.")
        job: Job = Job.parse_obj(job_data)
        resources: List[WebResource] = job.resources
        print(f'Processing {len(resources)} resources.')
        print(f'Downloading...')
        web_content: List[WebContent] = fetch_resource_batch(resources)
        print(f'Parsing contents...')
        parsed: List[ParsedContentUnion] = [parse(content) for content in web_content]
        return [
            parsed_content.model_dump(stringify_datetime=True, stringify_object_id=True)
            for parsed_content in parsed
        ]

    @task
    def create_embeddings(parsed_data):
        print('Creating embeddings...')
        return parsed_data

    @task
    def create_feature_extractions(parsed_data):
        print('Creating features...')
        return parsed_data

    @task
    def create_documents():
        pass

    @task
    def delete_old_documents():
        pass

    @task
    def upload_documents():
        pass

    @task
    def update_job_data():
        pass
