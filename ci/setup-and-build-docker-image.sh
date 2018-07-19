
# Install qemu-user-static
sudo apt-get install -y qemu-user-static
sudo docker run --rm --privileged multiarch/qemu-user-static:register --reset

# Download source code
echo "TODO switch to our repo. the Dockerfile in official repo need to patched"
git config --global credential.helper store
echo "https://BamvorZhang:gRt6UhC4WjnCjRmKThsv@bitbucket.org" >> ~/.git-credentials
go get -d -u -v bitbucket.org/ipfsbit/go-ipfs

echo Build docker images
cd ~/go/src/bitbucket.org/ipfsbit/go-ipfs
cp -p /usr/bin/qemu-arm-static .
sudo docker build . --file Dockerfile.armv7 -t bamvor/go-ipfs-armv7:latest

