#!/bin/bash

ARCH=arm64
CROSS_COMPILE=aarch64-linux-gnu-

#dependency
#library: libpopt.so, libpcap.so
#header: popt.h
BASE=/home/bamvor/works_hdd/source/kernel/kselftest_depandency/arm64
if [ X$ARCH = Xarm64 ]; then
	CFLAGS="-L$BASE/usr/lib64 -I$BASE/usr/include"
fi

usage()
{
	echo $0 --kerenl tag_for_kernel --kselftes tag_for_kselftest --source /path/to/your/kernel/source
	exit
}

enable_config()
{
	CFG=$1
	grep "^${CFG}=[ym]$" .config > /dev/null
	if [ "$?" = "0" ]; then
		echo "config $CFG is already exist"
		return
	fi
	#"# CONFIG_KDBUS is not set"
	grep "^#\ ${CFG}\ is\ not\ set$" .config > /dev/null
	if [ "$?" = "0" ]; then
		sed -i "s/^#\ ${CFG}\ is\ not\ set$/${CFG}=y/g" .config
	else
		echo ${CFG}=y >> .config
	fi
	echo "enable $CFG"
}

disable_config()
{
	CFG=$1
	#"# CONFIG_KDBUS is not set"
	grep "^#\ ${CFG}\ is\ not\ set$" .config > /dev/null
	if [ "$?" = "0" ]; then
		echo "config $CFG is already disable"
		return
	fi
	grep "^#${CFG}=[ym]$" .config > /dev/null
	if [ "$?" = "0" ]; then
		sed -i "s/^${CFG}=[ym]$/# ${CFG} is not set/g" .config
	else
		echo "# ${CFG} is not set" >> .config
	fi
	echo "disable $CFG"
}

select_kernel_config_for_kselftest()
{
	enable_config CONFIG_DEVPTS_MULTIPLE_INSTANCES
	enable_config CONFIG_TEST_STATIC_KEYS
	enable_config CONFIG_TEST_USER_COPY
	enable_config CONFIG_KDBUS
	enable_config CONFIG_TEST_FIRMWARE
	enable_config CONFIG_GENERIC_TRACER
	enable_config CONFIG_TRACING_SUPPORT
	enable_config CONFIG_FTRACE
	enable_config CONFIG_FUNCTION_TRACER
	enable_config CONFIG_FUNCTION_GRAPH_TRACER
	enable_config CONFIG_IRQSOFF_TRACER
	enable_config CONFIG_PREEMPT_TRACER
	enable_config CONFIG_SCHED_TRACER
	enable_config CONFIG_FTRACE_SYSCALLS
	enable_config CONFIG_TRACER_SNAPSHOT
	enable_config CONFIG_TRACER_SNAPSHOT_PER_CPU_SWAP
	enable_config CONFIG_BRANCH_PROFILE_NONE
	enable_config CONFIG_STACK_TRACER
	enable_config CONFIG_BLK_DEV_IO_TRACE
	enable_config CONFIG_DYNAMIC_FTRACE
	enable_config CONFIG_FUNCTION_PROFILER
	enable_config CONFIG_FTRACE_MCOUNT_RECORD
	enable_config CONFIG_TRACEPOINT_BENCHMARK
	enable_config CONFIG_RING_BUFFER_STARTUP_TEST
	enable_config CONFIG_TRACE_ENUM_MAP_FILE
	enable_config CONFIG_USER_NS
	enable_config CONFIG_BPF_SYSCALL
	enable_config CONFIG_TEST_BPF
	disable_config CONFIG_PROFILE_ANNOTATED_BRANCHES
	disable_config CONFIG_PROFILE_ALL_BRANCHES
	disable_config CONFIG_PROBE_EVENTS
	disable_config CONFIG_FTRACE_STARTUP_TEST
	disable_config CONFIG_RING_BUFFER_BENCHMARK
	#disable the useless new config
	disable_config CONFIG_NET_DROP_MONITOR
}

build_kernel()
{
	TAG=$1
	SOURCE=$2
	INSTALL=$3

	echo $ARCH, $CROSS_COMPILE

	cd $SOURCE
	echo "checkout to $TAG"
	STATUS=`git status --porcelain | grep -v ?`
	if [ X"$STATUS" != X ]; then
		echo "working tree does not clean, exit"
		echo "exit because working tree does not clean"
		exit 1
	fi
	git checkout -f $TAG

	echo "make distclean"
	make distclean > /dev/null || (echo "build failed"; exit 1)
	echo "make defconfig"
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE defconfig > /dev/null || (echo "build failed"; exit 1)
	echo "select kernel config for kselftest"
	select_kernel_config_for_kselftest
	echo "build and install kernal and modules"
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE Image dtbs -j8 > /dev/null || (echo "build failed"; exit 1)
	cp -p arch/$ARCH/boot/Image $INSTALL
	cp -pr arch/$ARCH/boot/dts $INSTALL
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE modules -j8 > /dev/null || (echo "build failed"; exit 1)
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE INSTALL_MOD_PATH=$INSTALL modules_install > /dev/null || (echo "build failed"; exit 1)

	cd -
}

build_kselftest()
{
	TAG=$1
	SOURCE=$2
	INSTALL=$3

	echo $ARCH, $CROSS_COMPILE

	cd $SOURCE

	if [ X$TAG != XCURRENT ]; then
		echo "checkout to $TAG"
		STATUS=`git status --porcelain | grep -v ?`
		if [ X"$STATUS" != X ]; then
			echo "working tree does not clean, exit"
			exit 1
		fi
		git checkout -f $TAG
	fi

	echo "build and install kselftest"
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE INSTALL_HDR_PATH=$SOURCE/usr/ headers_install -j8 > /dev/null || (echo "build failed"; exit 1)
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE CFLAGS="$CFLAGS" -C tools/testing/selftests #> /dev/null || (echo "build failed"; exit 1)
	make ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE CFLAGS="$CFLAGS" INSTALL_PATH=$INSTALL/kselftest -C tools/testing/selftests install #> /dev/null || (echo "build failed"; exit 1)

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
	--kselftest)
		KSELFTEST=$2
		shift 2
		;;
	--source)
		SOURCE=$(realpath $2)
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

if [ X$KERNEL = X ] || [ X$KSELFTEST = X ] || [ X$SOURCE = X ]; then
	echo "missing parameter"
	usage
	exit 1
fi
echo $KERNEL, $KSELFTEST, $SOURCE
echo "Whether tag and path is valid:"
if [ ! -d $SOURCE/.git ]; then
	echo "$SOURCE is not a git repo"
	exit 1
fi
if [ X$KERNEL != XCURRENT ]; then
	git --git-dir $SOURCE/.git rev-list $KERNEL --max-count=1  2>/dev/null
	if [ X$? != X0 ]; then
		echo "$KERNEL does not exist in $SOURCE"
		exit 1
	fi
fi
if [ X$KSELFTEST != XCURRENT ]; then
	git --git-dir $SOURCE/.git rev-list $KSELFTEST --max-count=1  2>/dev/null
	if [ X$? != X0 ]; then
		echo "$KSELFTEST does not exist in $SOURCE"
		exit 1
	fi
fi

INSTALL=$PWD
INSTALL+="/"
INSTALL+=`date +kselftest_%y%m%d_%H%M`
mkdir -p $INSTALL

build_kernel $KERNEL $SOURCE $INSTALL
build_kselftest $KSELFTEST $SOURCE $INSTALL

echo "SUCCESSFUL"

