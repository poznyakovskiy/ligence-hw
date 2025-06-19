# Prerequisites
This solution is designed to run on Ubuntu, it has been tested on Ubuntu 24.04.1 LTS. You will need the following packages:
```
python3 postgresql postgresql-contrib redis
```

Ensure that Redis is started:

```
sudo systemctl start redis
```

# Installation
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