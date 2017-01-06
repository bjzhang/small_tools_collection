#!/bin/bash


TEMP=`mktemp --tmpdir`
./gen_config.sh --enable A1 --disable BBB --disable "CC D4" --module E5 --module F6 -o $TEMP
diff $TEMP frag_test_golden
if [ X$? = X0 ]; then
	echo "PASS"
else
	echo "FAIL"
fi
rm $TEMP
