
# Install qemu-user-static
sudo apt-get install -y qemu-user-static
sudo docker run --rm --privileged multiarch/qemu-user-static:register --reset

# Download source code
echo "TODO switch to our repo. the Dockerfile in official repo need to patched"
go get -d -u github.com/ipfs/go-ipfs

echo Build docker images
cd go/src/github.com/ipfs/go-ipfs
cp -p /usr/bin/qemu-arm-static .
sudo docker build . --file Dockerfile.armv7 -t bamvor/go-ipfs-armv7:latest

