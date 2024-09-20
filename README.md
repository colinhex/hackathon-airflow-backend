
# Vision One Pager

![image](./docs/airflow-backend-architecture-vision.png)

# Setup

## Local Development
Set up a virtualenv and install requirements:
```shell
python venv .venv
```
```shell
source .venv/bin/activate
```
```shell
pip install -r requirements.txt
```

* Mark directories as sources root. (If in IDE)
```
/dags
/plugins
```

## Environment
Copy the file `example.env` to `.env` and set your environment variables.


## Deployment in Docker
1. Execute the `setup.sh` script with docker running on your system.
2. After initialisation (It will tell you to login when its done.), open the airflow webserver UI and add connections under `Admin -> Connections`.

![image](./docs/airflow-webui-connection-setup-1.png)
![image](./docs/airflow-webui-connection-setup-2.png)
![image](./docs/airflow-webui-connection-setup-3.png)
![image](./docs/airflow-webui-connection-setup-4.png)


