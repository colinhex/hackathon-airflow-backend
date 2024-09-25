from datetime import datetime
from typing import Any

from airflow.models import DagRun, DagModel
from airflow.utils.db import provide_session
from airflow.utils.state import DagRunState
from typing_extensions import Optional, List

from unibas.common.model.model_time import DateResult


@provide_session
def get_latest_successful_dag_run_date_or_none(dag_id: str, session: Optional[Any] = None) -> DateResult:
    """
    Retrieve the start date of the latest successful DAG run for a given DAG ID.

    Args:
        dag_id (str): The ID of the DAG to search for.
        session (Session): The SQLAlchemy session to use for the query.

    Returns:
        Optional[datetime]: The start date of the latest successful DAG run, or None if no successful run is found.

    Raises:
        ValueError: If there is an error retrieving the latest successful DagRun.
    """
    try:
        dag_runs: List[DagRun] = session.query(DagRun).filter(DagRun.dag_id == dag_id).all()
        dag_runs.sort(key=lambda x: x.execution_date, reverse=True)
        latest_successful_dag_run: DagRun | None = None
        for dag_run in dag_runs:
            if dag_run.get_state() == DagRunState.SUCCESS:
                latest_successful_dag_run = dag_run
                break
        if latest_successful_dag_run is None:
            print(f'No successful dag run found, returning none and let the operator choose a start date.')
            return DateResult()
        return DateResult(date=latest_successful_dag_run.start_date)
    except Exception as e:
        raise ValueError({'Could not retrieve latest successful DagRun': str(e)})


@provide_session
def get_dag_start_date(dag_id, session: Optional[Any] = None) -> DateResult:
    dag_model = session.query(DagModel).filter(DagModel.dag_id == dag_id).first()
    if dag_model:
        return DateResult(date=dag_model.start_date)
    return DateResult()

