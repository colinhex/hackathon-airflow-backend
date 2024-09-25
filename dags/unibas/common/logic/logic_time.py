from datetime import datetime

from airflow.models import DagRun
from airflow.utils.state import DagRunState
from typing_extensions import Optional, List


def get_latest_successful_dag_run_date_or_none(dag_id: str) -> Optional[datetime]:
    """
    Retrieve the start date of the latest successful DAG run for a given DAG ID.

    Args:
        dag_id (str): The ID of the DAG to search for.

    Returns:
        Optional[datetime]: The start date of the latest successful DAG run, or None if no successful run is found.

    Raises:
        ValueError: If there is an error retrieving the latest successful DagRun.
    """
    try:
        dag_runs: List[DagRun] = DagRun.find(dag_id=dag_id)
        dag_runs.sort(key=lambda x: x.execution_date, reverse=True)
        latest_successful_dag_run: DagRun | None = None
        for dag_run in dag_runs:
            if dag_run.get_state() == DagRunState.SUCCESS:
                latest_successful_dag_run = dag_run
                break
        if latest_successful_dag_run is None:
            print(f'No successful dag run found, returning none and let the operator choose a start date.')
            return
        return latest_successful_dag_run.start_date
    except Exception as e:
        raise ValueError({'Could not retrieve latest successful DagRun': str(e)})