#!/bin/bash

TEMP=`getopt -o h --long disable: --long enable: --long module: --long test -n '$0' -- "$@"`

if [ "$?" != "0" ]; then
	echo "Parameter process failed, Terminating..." >&2
	exit 1
fi

eval set -- "$TEMP"

while true; do
	case "$1" in
	--disable)
		DISABLE+="$2,"
		shift 2
		;;
	--enable)
		ENABLE+="$2,"
		shift 2
		;;
	-h)
		usage
		exit 0
		;;
	--module)
		MODULE+="$2,"
		shift 2
		;;
	--test)
		IS_TEST=1
		shift 1
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

KERNEL=$1
#Support $2 and $3 for enable and disable repectively. Keep backward
#compatability. There were no MODULE at that time.
if [ "X$ENABLE" != X ]; then
	ENABLE="--enable $ENABLE"
elif [ X$2 != X ]; then
	ENABLE="--enable $2"
fi
if [ "X$DISABLE" != X ]; then
	DISABLE="--disable $DISABLE"
elif [ X$3 != X ]; then
	DISABLE="--disable $3"
fi
if [ "X$MODULE" != X ]; then
	MODULE="--module $MODULE"
fi

echo "compile $KERNEL $ENABLE $DISABLE $MODULE"
sleep 1

cd $KERNEL
make ARCH=arm64 distclean
make ARCH=arm64 defconfig
gen_config.sh $ENABLE $DISABLE $MODULE -o frag_config
ARCH=arm64 ./scripts/kconfig/merge_config.sh .config frag_config
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j4 Image dtbs modules
rm usr/lib/* -rf
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j4 modules_install INSTALL_MOD_PATH=$PWD/usr
rm $PWD/usr/lib/modules/*/build
rm $PWD/usr/lib/modules/*/source
