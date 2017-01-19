#!/bin/bash

KERNEL=$1
if [ X$2 != X ]; then
	ENABLE="--enable $2"
fi
if [ X$3 != X ]; then
	DISABLE="--disable $3"
fi

echo "compile $KERNEL $ENABLE $DISABLE"
sleep 1

cd $KERNEL
make ARCH=arm64 distclean
make ARCH=arm64 defconfig
gen_config.sh $ENABLE $DISABLE -o frag_config
ARCH=arm64 ./scripts/kconfig/merge_config.sh .config frag_config
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j4 Image dtbs modules
rm usr/lib/* -rf
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j4 modules_install INSTALL_MOD_PATH=$PWD/usr
rm $PWD/usr/lib/modules/*/build
rm $PWD/usr/lib/modules/*/source
