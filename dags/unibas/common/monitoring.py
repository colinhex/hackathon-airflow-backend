from airflow.models import DagRun
from airflow.utils.state import DagRunState
from pymongo.results import InsertManyResult
from toolz import partition_all

from unibas.common.logic.logic_mongo import *
from unibas.common.logic.logic_parse import parse
from unibas.common.logic.logic_web_client import fetch_resource, fetch_resource_headers
from unibas.common.model.model_job import *
from unibas.common.model.model_parsed import ParsedContentUnion, ParsedSitemap
from unibas.common.model.model_resource import WebContent, WebResource, WebContentHeader


# Sitemap Monitors

def get_monitoring_date(dag_run: DagRun) -> Optional[datetime]:
    latest_successful_dag_runs: List[DagRun] = dag_run.get_latest_runs()
    latest_successful_dag_runs = [run for run in latest_successful_dag_runs if run.state == DagRunState.SUCCESS]
    if len(latest_successful_dag_runs) > 0:
        return None # latest_successful_dag_runs[0].start_date
    else:
        return None


def execute_sitemap_monitor(cutoff: datetime, sitemap_url: str, filter_paths: Optional[List[str]] = None) -> Optional[ParsedSitemap]:
    print(f"Fetching sitemap content from {sitemap_url}...")
    content: WebContent = fetch_resource(WebResource(loc=sitemap_url))
    parsed: ParsedContentUnion = parse(content)

    if not isinstance(parsed, ParsedSitemap):
        raise ValueError(f"Expected sitemap content, but got {type(parsed)}")
    sitemap: ParsedSitemap = parsed

    print(f"Filtering sitemap content modified after {cutoff.isoformat()} {'with filter paths ' + str(filter_paths) if filter_paths else 'without filter paths'}...")
    sitemap.content = WebContent.filter(sitemap.content, filter_paths=filter_paths, modified_after=cutoff)

    if len(sitemap.content) == 0:
        print("No sitemap content found.")
        return None
    print(f'Sitemap content found: {len(sitemap.content)} resources.')

    sitemap.filter_paths = filter_paths
    sitemap.modified_after = cutoff

    print('Returning sitemap content...')
    return sitemap


def execute_dam_monitor(cutoff: datetime, dam_uris: List[str]) -> Optional[List[WebContentHeader]]:
    print(f"Fetching DAM resource headers from {len(dam_uris)} URIs...")
    resources: List[WebResource] = [WebResource(loc=uri) for uri in dam_uris]
    headers: List[WebContentHeader] = fetch_resource_headers(resources)

    print(f"Filtering DAM resources modified after {cutoff.isoformat()}...")
    headers: List[WebContentHeader] = WebResource.filter(headers, modified_after=cutoff)

    if len(headers) == 0:
        print("No sitemap content found.")
        return None
    print(f'Updated DAM resources found: {len(headers)} resources.')

    return headers


def create_ingest_jobs_from_sitemap_resources(monitor_dag_id: str, sitemap: ParsedSitemap, job_size: int = 50) -> List[Job]:
    print('Partitioning sitemap content into ingest jobs...')
    job_resources: List[List[WebResource]] = [list(partition) for partition in partition_all(job_size, sitemap.content)]
    jobs: List[Job] = [Job(created_by=monitor_dag_id, resources=resources) for resources in job_resources]
    print(f'Created {len(jobs)} ingest jobs.')
    return jobs


def create_ingest_jobs_from_dam_resources(monitor_dag_id: str, dam_resources: List[WebContentHeader], job_size: int = 50) -> List[Job]:
    print('Partitioning DAM resources into ingest jobs...')
    job_resources: List[List[WebResource]] = [list(partition) for partition in partition_all(job_size, dam_resources)]
    jobs: List[Job] = [Job(created_by=monitor_dag_id, resources=resources) for resources in job_resources]
    print(f'Created {len(jobs)} ingest jobs.')
    return jobs


def upload_ingest_job_list(jobs: List[Job]) -> None:
    print(f'Uploading {len(jobs)} ingest jobs...')

    result: InsertManyResult = on_job_collection().insert_many(
        MongoModel.dump_all_models(jobs)
    )

    if result.acknowledged:
        print('Ingest jobs uploaded successfully.')
    else:
        raise ValueError(f'Failed to upload ingest jobs: {result}')
