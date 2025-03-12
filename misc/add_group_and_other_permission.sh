for f in `find $1 -name "*"`; do
	if [ -d "$f" ]; then
		#add Read the eXcution for directory
		chmod g+rx,o+rx "$f"
	else
		#add Read for regular file
		chmod g+r,o+r "$f"
	fi
done
