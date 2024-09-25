from datetime import datetime, timedelta

from airflow.decorators import dag, task

from unibas.common.monitoring import get_monitoring_date, execute_dam_monitor, \
    upload_ingest_job_list, create_ingest_jobs_from_dam_resources


def on_failure_callback(**context):
    print(f"Task {context['task_instance_key_str']} failed.")


dam_monitor_config = {
    "dag_display_name": "DAM Monitor BS",
    "dag_id": "dam_monitor_unibas_ch",
    "schedule_interval": "@weekly",
    "start_date": datetime(2024, 1, 1),
    "catchup": False,
    "job_size": 5,
    "dam_resources": [
        "https://www.unibas.ch/dam/jcr:756fd26f-ea10-4aa2-ad28-e433b15d42e0/Zulassungsrichtlinien%20Universitaet%20Basel-akademisches%20Jahr%202024_25.pdf",
        "https://www.unibas.ch/dam/jcr:c67b41e1-b339-4404-91ae-7a60a66a7a28/446_710_11.pdf",
        "https://www.unibas.ch/dam/jcr:a9ec4dd3-7e20-4dea-bed8-0c5898ab8bd6/446_720_00.pdf",
        "https://www.unibas.ch/dam/jcr:b66fd5f1-f778-4a4e-b554-d516e1714968/446_330_07.pdf"
    ],
    "tags": ["resource_monitor", "dam_monitor"],
    "default_args": {
        "owner": "unibas",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        'on_failure_callback': on_failure_callback
    },
}


@dag(
    dag_display_name="Dam Monitor UniBas",
    dag_id="dam_monitor_unibas_ch",
    schedule_interval=None,  # Adjust schedule as needed
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["resource_monitor"],
    default_args={
        "owner": "unibas",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        'on_failure_callback': on_failure_callback
    }
)
def dam_monitor():
    @task
    def get_last_monitoring_date(dag_id: str):
        return get_monitoring_date(dag_id)

    @task.short_circuit
    def monitor_dam(cutoff):
        return execute_dam_monitor(cutoff, dam_monitor_config['dam_resources'])

    @task
    def create_ingest_jobs(sitemap):
        return create_ingest_jobs_from_dam_resources(sitemap, dam_monitor_config['job_size'])

    @task
    def upload_ingest_jobs(jobs):
        upload_ingest_job_list(jobs)

    cutoff_result = get_last_monitoring_date(dag_id=dam_monitor_config['dag_id'])
    dam_result = monitor_dam(cutoff_result)
    ingest_jobs_result = create_ingest_jobs(dam_result)
    upload_ingest_jobs(ingest_jobs_result)


dam_monitor_dag = dam_monitor()



