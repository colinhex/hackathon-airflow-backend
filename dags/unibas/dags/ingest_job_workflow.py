from datetime import datetime, timedelta

from airflow.decorators import dag, task, task_group
from airflow.models import TaskInstance, DagRun
from toolz import concatv

from unibas.common.logic.logic_oai import create_embeddings_for_job, create_features_for_job
from unibas.common.logic.logic_parse import parse
from unibas.common.logic.logic_web_client import fetch_resource_batch
from unibas.common.processing import *


def on_failure_callback(task_instance: TaskInstance):
    job_id = task_instance.xcom_pull()
    print(f"Task {task_instance.task_id} failed for job_id {job_id}.")
    print(f"Error: {task_instance.error}")
    print(f"Updating job processing status.")
    on_job_failure(job_id)


def what_is_this(params):
    print(type(params))
    print(str(params))
    print(params)
    raise ValueError("This is a test error.")

@dag(
    dag_display_name="Ingest Job Workflow",
    dag_id="ingest_job_workflow",
    schedule_interval=None,  # External Trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingest_workflow"],
    default_args={
        "owner": "unibas",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        'on_failure_callback': on_failure_callback
    },
)
def ingest_job_workflow():

    @task_group(group_id='download_group')
    def download_group():

        @task(
            task_id="get_params",
            task_display_name="Get Params",
        )
        def get_params(dag_run: DagRun):
            job_id = dag_run.conf.get('job_id')
            if job_id is None:
                raise ValueError("No job_id found in dag_run.")
            return job_id

        @task(
            task_id="download_job_resources",
            task_display_name="Download Job Resources"
        )
        def download_job_resources(_task_id):
            job: Job = get_job_by_id(ObjectId(_task_id))
            job.resources = fetch_resource_batch(job.resources)
            update_job(job)
            return _task_id

        return download_job_resources(get_params())

    @task_group(
        group_id='parsing_group',
    )
    def parsing_group(job_id):

        @task(
            task_id="parse_job_resources",
            task_display_name="Parse Job Resources"
        )
        def parse_job_resources(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))
            job.resources = [parse(resource) for resource in job.resources]
            update_url_graph(job)
            return update_job(job)

        return parse_job_resources(job_id)

    @task_group(
        group_id='feature_extraction_group',
    )
    def feature_extraction_group(job_id):
        @task(
            task_id="create_embeddings",
            task_display_name="Create Embeddings"
        )
        def create_embeddings(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))
            return create_embeddings_for_job(job)

        @task(
            task_id="create_feature_extractions",
            task_display_name="Create Feature Extractions"
        )
        def create_feature_extractions(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))
            return create_features_for_job(job)

        @task(
            task_id="merge_features",
            task_display_name="Merge Features"
        )
        def merge_features(_job_id, embeddings, features):
            job: Job = get_job_by_id(ObjectId(_job_id))
            for idx, resource in enumerate(job.resources):
                job.resources[idx].embeddings = embeddings[str(resource.id)]
                job.resources[idx].features = features[str(resource.id)]
            return update_job(job)

        create_embeddings_task = create_embeddings(job_id)
        create_feature_extractions_task = create_feature_extractions(job_id)
        return merge_features(job_id, create_embeddings_task, create_feature_extractions_task)

    @task_group(group_id='document_formatting_group')
    def document_formatting_group(job_id):
        @task(
            task_id="create_documents",
            task_display_name="Create Documents"
        )
        def create_documents(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))
            job.resources = list(concatv(*[create_documents_for_resource(resource) for resource in job.resources]))
            return update_job(job)

        return create_documents(job_id)

    @task_group(group_id='ingest_group')
    def ingest_group(job_id):
        @task(
            task_id="delete_old_documents",
            task_display_name="Delete Old Documents"
        )
        def delete_old_documents(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))
            return delete_old_documents_from_vector_embeddings_collection(job)

        @task(
            task_id="upload_new_documents",
            task_display_name="Upload New Documents"
        )
        def upload_new_documents(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))
            return upload_new_documents_to_vector_embeddings_collection(job)


        delete_old_documents_task = delete_old_documents(job_id)
        upload_documents_task = upload_new_documents(job_id)

        delete_old_documents_task >> upload_documents_task

        return upload_documents_task

    @task(
        task_id="delete_job_data",
        task_display_name="Delete Job Data"
    )
    def delete_job_data(job_id):
        on_job_success(job_id)

    download_job_resources_tasks = download_group()
    parsing_group_tasks = parsing_group(download_job_resources_tasks)
    feature_extraction_group_tasks = feature_extraction_group(parsing_group_tasks)
    document_formatting_group_tasks = document_formatting_group(feature_extraction_group_tasks)
    ingest_group_tasks = ingest_group(document_formatting_group_tasks)
    delete_job_data(ingest_group_tasks)


x_job_ingest_dag = ingest_job_workflow()