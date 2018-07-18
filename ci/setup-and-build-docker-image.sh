# System update
echo y | sudo apt-get remove docker docker-engine docker.io
echo y | sudo apt-get update

# Install docker
echo y | sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
echo y | sudo apt-get update
echo y | sudo apt-get install docker-ce

# Install qemu-user-static
echo y | sudo apt-get install qemu-user-static
sudo docker run --rm --privileged multiarch/qemu-user-static:register --reset

# Install go
wget https://dl.google.com/go/go1.10.3.linux-amd64.tar.gz
tar zxf go1.10.3.linux-amd64.tar.gz
sudo cp -p go/bin/go* /usr/local/bin/
sudo mkdir /usr/local/go
rm -rf go

# Download source code
go get -d -u github.com/ipfs/go-ipfs

echo Build docker images
cd go/src/github.com/ipfs/go-ipfs
cp -p /usr/bin/qemu-arm-static .
sudo docker build . --file Dockerfile.armv7 -t bamvor/go-ipfs-armv7:latest

