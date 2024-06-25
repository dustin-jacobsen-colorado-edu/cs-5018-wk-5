#! /bin/bash

for envar in 'HOST', 'PORT', 'JAWSDB_URL', 'STATSD_HOST', 'STATSD_PORT', 'HOSTEDGRAPHITE_APIKEY', 'CLOUDAMQP_URL'; do
	if [ -z "$$envar" ] ; then
		echo "Fatal: missing mandatory environment variable $envar" 1>&2
		exit -1
	fi
done

exit 0
