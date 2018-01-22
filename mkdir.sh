#!/bin/bash

FWDIR="$(cd `dirname $0`/../; pwd)"

TOP=$FWDIR
ENV=${TOP##/*/env/}
ENV=${ENV%%/apps}

DIR_CONF=$TOP/all_dirs.conf

while read line
do
	DIR=${line##*=}
	KEY=${line%%=*}

	if [[ "$KEY" == *dir* || "$KEY" == *DIR* || "$KEY" == hdfs* ]]; then

		if [[ "$DIR" == hdfs://* ]]; then
		    echo "making hdfs dir: $DIR"
			hadoop fs -mkdir -p $DIR
		else
			echo "making dir: $DIR"
			mkdir -p $DIR
		fi
	fi
done < $DIR_CONF

exit 0

