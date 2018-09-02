echo "Update"
sudo yum clean all
sudo yum update
#sudo apt update
#sudo apt -y upgrade

echo "Install necessary software"
sudo yum -y install wget vim git

echo "Install go"
wget https://dl.google.com/go/go1.10.3.linux-amd64.tar.gz
tar -xvf go1.10.3.linux-amd64.tar.gz
sudo mv go /usr/local
sudo bash -c 'echo "GOROOT=/usr/local/go" >> /etc/profile'
sudo bash -c 'echo "PATH=/usr/local/go/bin:$PATH" >> /etc/profile'
#sudo apt install -y golang-go

echo "Install shadowsocks go"
go get -u -v github.com/shadowsocks/go-shadowsocks2

echo "Start ss server"
~/go/bin/go-shadowsocks2 -s 'ss://AEAD_CHACHA20_POLY1305:Suse*2018@96.45.183.183:8488' -verbose

echo "Start ss client"
echo "~/go/bin/go-shadowsocks2 -c 'ss://AEAD_CHACHA20_POLY1305:Suse*2018@96.45.183.183:8488' -verbose -socks :1080 -u -udptun :8053=8.8.8.8:53,:8054=8.8.4.4:53 -tcptun :8053=8.8.8.8:53,:8054=8.8.4.4:53"
