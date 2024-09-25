from datetime import datetime, timedelta

from airflow.decorators import dag, task

from unibas.common.monitoring import get_monitoring_date, execute_sitemap_monitor, \
    create_ingest_jobs_from_sitemap_resources, upload_ingest_job_list


def on_failure_callback(**context):
    print(f"Task {context['task_instance_key_str']} failed.")


sitemap_monitor_config = {
    "dag_display_name": "Sitemap Monitor unibas.ch",
    "dag_id": "sitemap_monitor_unibas_ch",
    "schedule_interval": "@daily",
    "start_date": datetime(2024, 1, 1),
    "catchup": False,
    "job_size": 50,
    "sitemap_url": "https://www.unibas.ch/de/sitemap.xml",
    "sitemap_filter": [
        "https://www.unibas.ch/de/Arbeiten-an-der-Universitaet-Basel/Leben-in-Basel.html",
        "https://www.unibas.ch/de/Universitaet/Administration-Services/Vizerektorat-Forschung/Nationale-und-Internationale-Zusammenarbeit/Welcome-Center.html",
        "https://www.unibas.ch/de/Studium/Bewerbung-Zulassung/Anmeldung/Bachelorstudium-mit-schweizerischem-Vorbildungsausweis/Verspaetete-Anmeldung-zum-Bachelorstudium-mit-schweizerischem-Vorbildungsausweis.html",
        "https://www.unibas.ch/de/Studium/Bewerbung-Zulassung/Anmeldung/Bachelorstudium-mit-auslaendischem-Vorbildungsausweis/Verspaetete-Anmeldung-zum-Bachelorstudium-mit-auslaendischem-Vorbildungsausweis.html",
        "https://www.unibas.ch/de/Studium/Bewerbung-Zulassung/Anmeldung/Masterstudium-ausser-Medizin-und-Pflegewissenschaft/Verspaetete-Anmeldung-zum-Masterstudium-mit-schweizerischem-Hochschulabschluss.html",
        "https://www.unibas.ch/de/Studium/Bewerbung-Zulassung/Zulassung/Medizin.html",
        "https://www.unibas.ch/de/Studium/Campus-Stories/wie-man-sich-am-besten-auf-den-eignungstest-fuer-das-medizinstudium-ems-vorbereitet.html",
        "https://www.unibas.ch/de/Studium/Im-Studium/Rueckmelden.html",
        "https://www.unibas.ch/de/Studium/Mobilitaet/Mobilitaet-Schweiz/Belegen-Studierende-anderer-Schweizer-Universitaeten.html",
        "https://www.unibas.ch/de/Studium/Im-Studium/Rueckmelden.html",
        "https://www.unibas.ch/de/Studium/Im-Studium/Datenabschrift.html",
        "https://www.unibas.ch/de/Studium/Bewerbung-Zulassung.html",
        "https://www.unibas.ch/de/Studium/Beratung/Soziales-Gesundheit/Behinderung-Krankheit.html",
        "https://www.unibas.ch/de/Studium/Im-Studium/"
    ],
    "tags": ["resource_monitor", "sitemap_monitor"],
    "default_args": {
        "owner": "unibas",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        'on_failure_callback': on_failure_callback
    },
}

@dag(
    dag_display_name=sitemap_monitor_config['dag_display_name'],
    dag_id=sitemap_monitor_config['dag_id'],
    schedule_interval=sitemap_monitor_config['schedule_interval'],
    start_date=sitemap_monitor_config['start_date'],
    catchup=sitemap_monitor_config['catchup'],
    tags=sitemap_monitor_config['tags'],
    default_args=sitemap_monitor_config['default_args']
)
def sitemap_monitor():
    @task
    def get_last_monitoring_date(dag_id: str):
        return get_monitoring_date(dag_id)

    @task.short_circuit
    def monitor_sitemap(cutoff):
        return execute_sitemap_monitor(cutoff, sitemap_monitor_config['sitemap_url'], sitemap_monitor_config['sitemap_filter'])

    @task
    def create_ingest_jobs(sitemap):
        return create_ingest_jobs_from_sitemap_resources(sitemap, sitemap_monitor_config['job_size'])

    @task
    def upload_ingest_jobs(jobs):
        upload_ingest_job_list(jobs)

    cutoff_result = get_last_monitoring_date(dag_id=sitemap_monitor_config['dag_id'])
    sitemap_result = monitor_sitemap(cutoff_result)
    ingest_jobs_result = create_ingest_jobs(sitemap_result)
    upload_ingest_jobs(ingest_jobs_result)


sitemap_monitor_dag = sitemap_monitor()



