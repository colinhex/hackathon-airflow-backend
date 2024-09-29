from datetime import datetime, timedelta

from airflow.configuration import AirflowConfigParser
from airflow.decorators import dag, task, task_group
from airflow.models import TaskInstance, DagRun
from airflow.operators.python import PythonOperator, get_current_context

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

            if check_for_document_chunks(job):
                print(f"Job {job.id} already has document chunks, skipping ahead.")
                return str(job.id)

            verify_resources_available(job)

            download_resources(job)

            update_job(job)
            verify_download_success(job)

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

            if check_for_document_chunks(job):
                print(f"Job {job.id} already has document chunks, skipping ahead.")
                return _job_id

            parse_resources(job)
            url_graph: UrlGraph = collect_links_into_graph_and_remove_from_attributes(job)

            update_job(job)
            verify_text_chunks_available(job)

            # Further handling for links.
            print(f"Processing URL Graph: {url_graph.model_dump_json(indent=2)}")

            return _job_id

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

            if check_for_document_chunks(job):
                print(f"Job {job.id} already has document chunks, skipping ahead.")
                return _job_id

            _embeddings = create_embeddings_for_job(job)

            verify_embeddings_available(job, _embeddings)

            return _embeddings

        @task(
            task_id="create_feature_extractions",
            task_display_name="Create Feature Extractions"
        )
        def create_feature_extractions(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))

            if check_for_document_chunks(job):
                print(f"Job {job.id} already has document chunks, skipping ahead.")
                return _job_id

            _features = extract_features_for_job(job)

            verify_feature_extraction_available(job, _features)

            _features = {resource_id: dump_all_models(feature) for resource_id, feature in _features.items()}
            return _features

        @task(
            task_id="merge_features",
            task_display_name="Merge Features"
        )
        def merge_features(_job_id, _embeddings, _features):
            job: Job = get_job_by_id(ObjectId(_job_id))

            if check_for_document_chunks(job):
                print(f"Job {job.id} already has document chunks, skipping ahead.")
                return _job_id

            # Merge embeddings and features
            for idx, resource in enumerate(job.resources):
                assert isinstance(resource, ParsedWebContentTextChunks)
                resource.embeddings = _embeddings[str(resource.id)]
                resource.features = _features[str(resource.id)]

            update_job(job)

            return _job_id

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

            if check_for_document_chunks(job):
                print(f"Job {job.id} already has document chunks, skipping ahead.")
                return _job_id

            create_chunk_document_from_job(job)

            update_job(job)
            verify_documents_available(job)

            return _job_id

        return create_documents(job_id)

    @task_group(group_id='ingest_group')
    def ingest_group(job_id):
        @task(
            task_id="delete_old_documents",
            task_display_name="Delete Old Documents"
        )
        def delete_old_documents(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))

            delete_old_documents_from_vector_embeddings_collection(job)

        @task(
            task_id="upload_new_documents",
            task_display_name="Upload New Documents"
        )
        def upload_new_documents(_job_id):
            job: Job = get_job_by_id(ObjectId(_job_id))

            upload_new_documents_to_vector_embeddings_collection(job)

            return _job_id


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