#!/bin/bash

usage()
{
	exit
}

build_kernel()
{
	TAG=$1
	SOURCE=$2
	INSTALL=$3

	cd $SOURCE

	echo "make distclean"
	make distclean > /dev/null || (echo "build failed"; exit 1)
	echo "make defconfig"
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE defconfig > /dev/null || (echo "build failed"; exit 1)
	echo "select kernel config for kselftest"
	ARCH=$ARCH ./scripts/kconfig/merge_config.sh .config ../config
	echo "build and install kernal and modules"
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE Image dtbs -j8 > /dev/null || (echo "build failed"; exit 1)
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE modules -j8 > /dev/null || (echo "build failed"; exit 1)
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE INSTALL_MOD_PATH=$INSTALL modules_install > /dev/null || (echo "build failed"; exit 1)

	cd -
}

TEMP=`getopt -o h --long kernel: --long kselftest: --long source: -n '$0' -- "$@"`

if [ "$?" != "0" ]; then
	echo "Parameter process failed, Terminating..." >&2
	exit 1
fi

eval set -- "$TEMP"

while true; do
	case "$1" in
	-h)
		usage
		exit 0
		;;
	--kernel)
		KERNEL=$2
		shift 2
		;;
	--source)
		SOURCE=$PWD
		SOURCE+="/"
		SOURCE+=$2
		shift 2
		;;
	--)
		shift
		break
		;;
	*)
		echo "internal error"
		exit 1
		;;
	esac
done

if [ X$KERNEL = X ] || [ X$SOURCE = X ]; then
	echo "missing parameter"
	usage
	exit 1
fi
echo $KERNEL, $KSELFTEST, $SOURCE

INSTALL=$PWD
INSTALL+="/"
INSTALL+=`date +kselftest_%y%m%d_%H%M`

ARCH=arm64
CROSS_COMPILE=aarch64-linux-gnu-
build_kernel $KERNEL $SOURCE $INSTALL
ARCH=arm
CROSS_COMPILE=arm-linx-gnueabihf-
build_kernel $KERNEL $SOURCE $INSTALL

echo "SUCCESSFUL"

