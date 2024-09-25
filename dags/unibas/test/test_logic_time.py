import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from airflow.models import DagRun
from airflow.utils.state import DagRunState

from unibas.common.logic.logic_time import get_latest_successful_dag_run_date_or_none


class TestGetLatestSuccessfulDagRunDateOrNone(unittest.TestCase):

    @patch('unibas.common.logic.logic_time.DagRun.find')
    def test_get_latest_successful_dag_run_date_or_none(self, mock_find):
        # Create mock DagRun objects
        dag_run_success = MagicMock(spec=DagRun)
        dag_run_success.get_state.return_value = DagRunState.SUCCESS
        dag_run_success.start_date = datetime(2023, 1, 1)
        dag_run_success.execution_date = datetime(2023, 1, 1)

        dag_run_failed = MagicMock(spec=DagRun)
        dag_run_failed.get_state.return_value = DagRunState.FAILED
        dag_run_failed.execution_date = datetime(2023, 1, 2)

        # Set the return value of DagRun.find
        mock_find.return_value = [dag_run_failed, dag_run_success]

        # Call the function
        result = get_latest_successful_dag_run_date_or_none('test_dag_id')

        # Assert the result
        self.assertEqual(result, datetime(2023, 1, 1))

    @patch('unibas.common.logic.logic_time.DagRun.find')
    def test_get_latest_successful_dag_run_date_or_none_no_success(self, mock_find):
        # Create mock DagRun objects
        dag_run_failed = MagicMock(spec=DagRun)
        dag_run_failed.get_state.return_value = DagRunState.FAILED
        dag_run_failed.execution_date = datetime(2023, 1, 2)

        # Set the return value of DagRun.find
        mock_find.return_value = [dag_run_failed]

        # Call the function
        result = get_latest_successful_dag_run_date_or_none('test_dag_id')

        # Assert the result is None
        self.assertIsNone(result)

    @patch('unibas.common.logic.logic_time.DagRun.find')
    def test_get_latest_successful_dag_run_date_or_none_exception(self, mock_find):
        # Set the return value of DagRun.find to raise an exception
        mock_find.side_effect = Exception('Test exception')

        # Call the function and assert it raises a ValueError
        with self.assertRaises(ValueError) as context:
            get_latest_successful_dag_run_date_or_none('test_dag_id')

        self.assertIn('Could not retrieve latest successful DagRun', str(context.exception))


if __name__ == '__main__':
    unittest.main()