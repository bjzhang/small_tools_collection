
CUR=`date +"%Y-%m-%dT%H:%M:%S"`
cp -p cliclick_date_time.txt date_time.txt
sed -ibak "s/date_time/$CUR/g" date_time.txt
rm date_time.txtbak
cliclick -f date_time.txt
rm date_time.txt
