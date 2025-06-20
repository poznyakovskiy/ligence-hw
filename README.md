# Run using Docker (recommended)
If you have Docker, simply run

```
docker-compose build
docker-compose up
```
The frontend will be available under http://localhost:8080. The generator service will be under http://localhost:8000, the verifier wil be under http://localhost:8001.

# Run on the host machine
## Prerequisites
This solution is designed to run on Ubuntu, it has been tested on Ubuntu 24.04.1 LTS. You will need the following packages:
```
python3 postgresql postgresql-contrib redis
```

Ensure that Redis is started:

```
sudo systemctl start redis
```

## Installation
Install required Python packages in the local environment:

``` sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

Add execution permissions to the `setup_db.sh` script

``` sh
chmod +x setup_db.sh
```

Run the script with

``` sh
./setup_db.sh
```