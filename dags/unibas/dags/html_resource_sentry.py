from datetime import datetime, timedelta

from airflow.decorators import dag, task
from toolz import concatv

from unibas.common.operations import *
from unibas.common.typing import SitemapQuery, all_to_dict


def on_failure_callback(**context):
    print(f"Task {context['task_instance_key_str']} failed.")


@dag(
    dag_display_name="HTML Resource Sentry",
    dag_id="html_resource_sentry",
    schedule_interval=None,  # Adjust schedule as needed
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["hackathon"],
    default_args={
        "owner": "unibas",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        'on_failure_callback': on_failure_callback
    }
)
def download_sentry_dag():
    @task
    def calculate_cutoff_date(dag_id):
        return TimeOps.get_latest_successful_dag_run_date_or_none(dag_id).dict()

    @task
    def query_bs_sitemap_for_html_resources(modified_after):
        return all_to_dict(SitemapOps.execute_sitemap_query(
            SitemapQuery(
                sitemap_url='https://www.bs.ch/sitemap.xml',
                start_paths=[
                    'https://www.bs.ch/themen/bildung-und-kinderbetreuung/hoehere-bildung-und-weiterbildung/'
                ],
                mod_after=IsoTime(**modified_after)
            )
        ))

    @task.short_circuit
    def concat_html_resources_and_verify(resources):
        result = []
        if len(resources) == 0:
            return None
        if isinstance(resources[0], List):
            for sub_list in resources:
                result.extend(sub_list)
        else:
            return resources
        if len(result) == 0:
            return None
        return result

    @task
    def collect_html_resources_into_batches(html_resources):
        return all_to_dict(GlueOps.batches_from_html_resources(
            dag_id='html_resource_sentry',
            html_resources=HtmlResource.from_serialised_list(html_resources),
            batch_size=25
        ))

    @task
    def upload_batches_for_processing(batches):
        print(MongoAtlas.conn_id)
        print(MongoAtlas.airflow_database)
        print(MongoAtlas.batch_collection)
        MongoOps.mongo_insert_many(MongoQuery(
            database=MongoAtlas.airflow_database,
            collection=MongoAtlas.batch_collection,
            query=batches
        ))

    # Task dependencies
    cutoff_date = calculate_cutoff_date('download_sentry')
    bs_html_resources = query_bs_sitemap_for_html_resources(cutoff_date)
    updated_html_resources = concat_html_resources_and_verify(bs_html_resources)
    html_resource_batches = collect_html_resources_into_batches(updated_html_resources)
    upload_batches_for_processing(html_resource_batches)


download_sentry_dag_instance = download_sentry_dag()