from datetime import timedelta

from airflow.decorators import dag, task

from unibas.common.model.model_utils import dump_all_models_json
from unibas.common.monitoring import *


def on_failure_callback(**context):
    print(f"Task {context['task_instance_key_str']} failed.")


dam_monitor_config = {
    "dag_display_name": "DAM Monitor unibas.ch",
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
    dag_display_name=dam_monitor_config['dag_display_name'],
    dag_id=dam_monitor_config['dag_id'],
    schedule_interval=dam_monitor_config['schedule_interval'],
    start_date=dam_monitor_config['start_date'],
    catchup=dam_monitor_config['catchup'],
    tags=dam_monitor_config['tags'],
    default_args=dam_monitor_config['default_args']
)
def dam_monitor():
    @task.short_circuit
    def monitor_dam(dag_run: DagRun):
        web_content_headers: List[WebContentHeader] = execute_dam_monitor(
            get_monitoring_date(dag_run) or dam_monitor_config['start_date'],
            dam_monitor_config['dam_resources'],
        )
        if not web_content_headers:
            return None
        return dump_all_models_json(web_content_headers)

    @task
    def create_ingest_jobs(content_headers):
        headers: List[WebContentHeader] = [WebContentHeader.parse_obj(header) for header in content_headers]
        jobs: List[Job] = create_ingest_jobs_from_dam_resources(dam_monitor_config['dag_id'], headers, dam_monitor_config['job_size'])
        upload_ingest_job_list(jobs)

    monitor = monitor_dam()
    create_ingest_jobs(monitor)


dam_monitor_dag = dam_monitor()



