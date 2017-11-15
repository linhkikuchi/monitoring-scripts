#!/bin/bash

# This nagios plugin checks to see if rabbitmq-server is running, and if
# the rabbitmq cluster is in a partitioned state
#

E_SUCCESS="0"
E_WARNING="1"
E_CRITICAL="2"
E_UNKNOWN="3"
srvc="rabbitmq-server"

# Sanity check
sudo /etc/init.d/$srvc status > /dev/null 2>&1

if [ $? -ne 0 ]; then
        echo "rabbitmq-server is not running"
        exit ${E_UNKNOWN}
fi

status=`sudo rabbitmqctl cluster_status`
if [ $? -ne 0 ]; then
        echo "rabbitmqctl status unknown"
        exit ${E_UNKNOWN}
fi

#echo $status
partitions=`echo $status |  grep -o "partitions,\[[^]]\+\]"`

if [ "$partitions" ] ; then
        echo "Partitions exist!"
        exit ${E_CRITICAL}
else
        echo "Ok - No Partitions Found"
        exit ${E_SUCCESS}
fi
