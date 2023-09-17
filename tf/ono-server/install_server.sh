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
sudo docker pull pullenti/pullenti-server
sudo docker run -d --name pullenti --platform linux/amd64 -v /tmp/ner/pullenti-server/conf.xml:/app/conf.xml -p 8081:8080 pullenti/pullenti-server

# install pullenti client
cp /tmp/ner/pullenti-client-setup.py ./pullenti-client/setup.py
cp /tmp/ner/pullenti-client-demo.py ./pullenti-client/demo.py
python3 -m venv ./pullenti-client/vevn
python3 -m pip install -e ./pullenti-client
