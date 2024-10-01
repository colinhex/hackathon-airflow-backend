from datetime import datetime, timedelta

from airflow.decorators import task
from airflow.models import TaskInstance
from airflow.models.dag import dag
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.mongo.sensors.mongo import MongoSensor

from unibas.common.logic.logic_mongo import *


def on_failure_callback(task_instance: TaskInstance):
    print(f"Error: {task_instance.task_id}")


@dag(
    dag_display_name="Ingest Job Sensor",
    dag_id="ingest_job_sensor",
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
def ingest_job_sensor():

    mongo_sensor = MongoSensor(
        task_display_name="Job Sensor",
        task_id="job_sensor",
        mongo_conn_id=MongoAtlasEnvVariables.conn_id,
        mongo_db=MongoAtlasEnvVariables.airflow_database,
        collection=MongoAtlasEnvVariables.job_collection,
        query={
            # Does a job exist that is not processing and has been tried less than 3 times?
            'tries': {
                '$lt': 3
            },
            'processing': False
        },
        poke_interval=30,
        timeout=timedelta(days=3),
        mode="poke",
    )

    @task(
        task_id="get_sensed_job_id",
        task_display_name="Get Sensed Job Id",
    )
    def get_sensed_job_id():
        result = on_job_collection().find_one_and_update(
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
            projection={
                '_id': True
            },
        )

        if result is None:
            raise ValueError('No job found.')

        return str(result['_id'])

    job_id = get_sensed_job_id()

    ingest_trigger = TriggerDagRunOperator(
        task_display_name="Ingest Trigger",
        task_id='trigger_ingest',
        trigger_dag_id='ingest_job_workflow',
        conf={'job_id': job_id},
    )

    # Triggers itself after sleeping. Will then poke directly.
    self_trigger = TriggerDagRunOperator(
        task_display_name="Self Trigger",
        task_id='trigger_sensor',
        trigger_dag_id='ingest_job_sensor',
    )

    mongo_sensor >> job_id >> ingest_trigger >> self_trigger


x_job_ingest_dag = ingest_job_sensor()
