#!/bin/bash

usage()
{
	echo "$0 --enable AARCH32_EL0 --enable ARM64_ILP32 --disable AAA --module XXX -o output_frag_config"
}

TEMP=`getopt -o ho: --long disable: --long enable: --long module: -n '$0' -- "$@"`

if [ "$?" != "0" ]; then
	echo "Parameter process failed, Terminating..." >&2
	exit 1
fi

eval set -- "$TEMP"

while true; do
	case "$1" in
	--disable)
		DISABLE+="$2 "
		shift 2
		;;
	--enable)
		ENABLE+="$2 "
		shift 2
		;;
	-h)
		usage
		exit 0
		;;
	--module)
		MODULE+="$2 "
		shift 2
		;;
	-o)
		OUTPUT=$2
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

ENABLE=`echo ${ENABLE} | tr "," " "`
DISABLE=`echo ${DISABLE} | tr "," " "`
MODULE=`echo ${MODULE} | tr "," " "`
TEMP=`mktemp --tmpdir`
for e in $ENABLE; do
	echo "CONFIG_$e=y" >>$TEMP
done
for d in $DISABLE; do
	echo "# CONFIG_$d is not set" >>$TEMP
done
for m in $MODULE; do
	echo "CONFIG_$m=m" >>$TEMP
done

if [ X"$OUTPUT" = X ]; then
	cat $TEMP
	rm $TEMP
else
	mv $TEMP $OUTPUT
fi

