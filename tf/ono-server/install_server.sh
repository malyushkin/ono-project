#!/bin/bash

sudo apt update
sudo apt install -y software-properties-common

# install docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo apt install -y docker-ce

# update python to 3.11
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-distutils
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2
sudo update-alternatives --set python3 /usr/bin/python3.11

# install pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
python3 -m pip install virtualenv

# install pullenti server
docker network create --driver bridge pullenti-net
docker pull pullenti/pullenti-server
docker run -d \
  --name pullenti \
  --network pullenti-net \
  --platform linux/amd64 \
  -v /tmp/ner/pullenti-server/conf.xml:/app/conf.xml \
  -p 8081:8080 \
  pullenti/pullenti-server

# install pullenti client
mkdir -p "/home/ubuntu/pullenti-client"
mkdir -p "/home/ubuntu/pullenti-client/notebooks"
cp /tmp/ner/demo/setup.py /home/ubuntu/pullenti-client/setup.py
cp /tmp/ner/demo/script.py /home/ubuntu/pullenti-client/demo.py
cp /tmp/ner/demo/notebook.ipynb /home/ubuntu/pullenti-client/notebooks/demo.ipynb

python3 -m venv ./pullenti-client/vevn
python3 -m pip install -e ./pullenti-client

# install jupyter notebook
docker pull jupyter/minimal-notebook
# run a container with `1234` password
docker run -d \
  --name notebook \
  --network pullenti-net \
  --platform linux/amd64 \
  --user root \
  -e CHOWN_HOME=yes \
  -e CHOWN_HOME_OPTS="-R" \
  -v "/home/ubuntu/pullenti-client/notebooks":/home/jovyan/work \
  -p 8888:8888 \
  jupyter/minimal-notebook \
  start-notebook.sh --PasswordIdentityProvider.hashed_password='argon2:$argon2id$v=19$m=10240,t=10,p=8$h8jqHXGWAPwaG67oAHmKhQ$mvxwYBpVKvzUn00a+8As3njo4qgEyODAQ5VoUbIHlQw'

docker exec -it notebook bash -c "sudo apt-get update"
docker exec -it notebook bash -c "sudo apt install -y graphviz"

# install postgres
sudo apt-get -y install postgresql-12 postgresql-contrib-12
sudo -u postgres -i psql --command "CREATE ROLE server SUPERUSER LOGIN PASSWORD 'server';"
sudo -u postgres -i psql --command "CREATE DATABASE ono_db OWNER 'server';"
sudo -u postgres -i psql --command "CREATE EXTENSION IF NOT EXISTS 'uuid-ossp';"
sudo -u postgres -i psql -d ono_db -a -f /tmp/ner/db.sql

# edit config
cp /etc/postgresql/12/main/postgresql.conf{,.bak}
cp /etc/postgresql/12/main/pg_hba.conf{,.bak}
sudo sed -i "64 i listen_addresses = '*'" /etc/postgresql/12/main/postgresql.conf
sudo sh -c "echo host all all 0.0.0.0/0 md5 >> /etc/postgresql/12/main/pg_hba.conf"

# restart postgresql
sudo systemctl restart postgresql