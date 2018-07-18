# System update
sudo apt-get remove -y docker docker-engine docker.io
sudo apt-get update -y

# Install docker
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update -y
sudo apt-get install -y docker-ce

# Install docker-compse
sudo apt-get install -y docker-compose

# Install go
wget https://dl.google.com/go/go1.10.3.linux-amd64.tar.gz
tar zxf go1.10.3.linux-amd64.tar.gz
sudo cp -p go/bin/go* /usr/local/bin/
sudo mkdir /usr/local/go
sudo rm -rf go

