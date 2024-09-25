from datetime import datetime
from typing import Dict

from pymongo.results import InsertManyResult
from toolz import partition_all
from typing_extensions import Optional, List

from unibas.common.environment.variables import MongoAtlasEnvVariables
from unibas.common.logic.logic_airflow import get_latest_successful_dag_run_date_or_none, get_dag_start_date
from unibas.common.logic.logic_mongo import mongo_insert_many
from unibas.common.logic.logic_parse import parse
from unibas.common.logic.logic_web_client import fetch_resource, fetch_resource_headers
from unibas.common.model.model_job import Job
from unibas.common.model.model_mongo import MongoQuery
from unibas.common.model.model_parsed import ParsedContentUnion, ParsedWebContentXmlSitemapResult
from unibas.common.model.model_resource import WebContent, WebResource, WebContentHeader
from unibas.common.model.model_time import DateResult


# Sitemap Monitors

def get_monitoring_date(dag_id: str) -> Dict:
    print('Getting last successful run date...')
    monitoring_date: DateResult = get_latest_successful_dag_run_date_or_none(dag_id)
    if monitoring_date is None:
        print('No last monitoring date found, getting DAG start date...')
        monitoring_date = get_dag_start_date(dag_id).raise_if_empty()
    return monitoring_date.model_dump(stringify_datetime=True)


def execute_sitemap_monitor(cutoff: Dict, sitemap_url: str, filter_paths: Optional[List[str]] = None) -> Optional[Dict]:
    print(f"Fetching sitemap content from {sitemap_url}...")
    content: WebContent = fetch_resource(WebResource(loc=sitemap_url))
    parsed: ParsedContentUnion = parse(content)

    if not isinstance(parsed, ParsedWebContentXmlSitemapResult):
        raise ValueError(f"Expected sitemap content, but got {type(parsed)}")
    sitemap: ParsedWebContentXmlSitemapResult = parsed

    cutoff_date: datetime = DateResult.parse_obj(cutoff).date
    print(f"Filtering sitemap content modified after {cutoff_date.isoformat()} {'with filter paths ' + str(filter_paths) if filter_paths else 'without filter paths'}...")
    sitemap.content = WebContent.filter(sitemap.content, filter_paths=filter_paths, modified_after=cutoff_date)

    if len(sitemap.content) == 0:
        print("No sitemap content found.")
        return None
    print(f'Sitemap content found: {len(sitemap.content)} resources.')

    sitemap.filter_paths = filter_paths
    sitemap.modified_after = cutoff_date

    print('Returning sitemap content...')
    return sitemap.model_dump(
        stringify_object_id=True,
        stringify_datetime=True
    )


def execute_dam_monitor(cutoff: Dict, dam_uris: List[str]) -> Optional[List[Dict]]:
    print(f"Fetching DAM resource headers from {len(dam_uris)} URIs...")
    resources: List[WebResource] = [WebResource(loc=uri) for uri in dam_uris]
    headers: List[WebContentHeader] = fetch_resource_headers(resources)

    cutoff_date: datetime = DateResult.parse_obj(cutoff).date
    print(f"Filtering DAM resources modified after {cutoff_date.isoformat()}...")

    headers: List[WebContentHeader] = WebResource.filter(headers, modified_after=cutoff_date)

    if len(headers) == 0:
        print("No sitemap content found.")
        return None
    print(f'Updated DAM resources found: {len(headers)} resources.')

    return [header.model_dump(
        stringify_object_id=True,
        stringify_datetime=True
    ) for header in headers]


def create_ingest_jobs_from_sitemap_resources(sitemap: Dict, job_size: int = 50) -> List[Dict]:
    sitemap: ParsedWebContentXmlSitemapResult = ParsedWebContentXmlSitemapResult.parse_obj(sitemap)
    print('Partitioning sitemap content into ingest jobs...')
    job_resources: List[List[WebResource]] = [list(partition) for partition in partition_all(job_size, sitemap.content)]
    jobs: List[Job] = [Job(resources=resources) for resources in job_resources]
    print(f'Created {len(jobs)} ingest jobs.')
    return [job.model_dump(
        stringify_object_id=True,
        stringify_datetime=True
    ) for job in jobs]


def create_ingest_jobs_from_dam_resources(dam_resources: List[Dict], job_size: int = 50) -> List[Dict]:
    dam_resources: List[WebContentHeader] = [WebContentHeader.parse_obj(resource) for resource in dam_resources]
    print('Partitioning DAM resources into ingest jobs...')
    job_resources: List[List[WebResource]] = [list(partition) for partition in partition_all(job_size, dam_resources)]
    jobs: List[Job] = [Job(resources=resources) for resources in job_resources]
    print(f'Created {len(jobs)} ingest jobs.')
    return [job.model_dump(
        stringify_object_id=True,
        stringify_datetime=True
    ) for job in jobs]


def upload_ingest_job_list(jobs: List[Dict]) -> None:
    jobs: List[Job] = [Job.parse_obj(job) for job in jobs]
    result: InsertManyResult = mongo_insert_many(MongoQuery(
        database=MongoAtlasEnvVariables.airflow_database,
        collection=MongoAtlasEnvVariables.batch_collection,
        query=jobs
    ))
    if result.acknowledged:
        print('Ingest jobs uploaded successfully.')
    else:
        raise ValueError(f'Failed to upload ingest jobs: {result}')
