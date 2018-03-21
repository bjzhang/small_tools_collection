
if [ $# -lt 3 ]; then
    echo "Usage: $0 interface_name ip_address gateway"
    echo "example: bash ./set_ip.sh ens5f1 192.168.0.146 192.168.0.1"
    exit 1
fi
echo "please modify the position in the beginning of set_ip.txt"
read
interface=$1
address=$2
gateway=$3

cp -p cliclick_set_ip.txt set_ip.txt
sed -ibak "s/dummy/$interface/g" set_ip.txt
sed -ibak "s/ip_addr/$address/g" set_ip.txt
sed -ibak "s/ip_gateway/$gateway/g" set_ip.txt
rm set_ip.txtbak
cliclick -f set_ip.txt
