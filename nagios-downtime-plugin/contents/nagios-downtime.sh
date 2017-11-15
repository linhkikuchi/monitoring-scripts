#!/bin/bash

NAGIOS_LIST=( server_name )
NAGIOS_PORT=6315
# Both in seconds
CONNECTION_TIMEOUT=15
MAX_TIME=45
# Exit status 1 is not on any servers, status 2 is server failed to put into downtime.

function colorprint {
        echo -e "${1}$2${NC}"
}

function was_json_successful {
	json=$1
	count=$(echo "$json" | grep -o "\"success\": true" | wc -l)
	# Returns the count of success:true in the json, a successful post should have 1 occurence
	echo $count
}

function json_post {
	result=$(curl -H "Content-Type: application/json" -d  "$1" $2 -sS --connect-timeout $CONNECTION_TIMEOUT --max-time $MAX_TIME)
	echo $(was_json_successful "$result")
}
function get_server {
	filename="/tmp/$1-$$.tmp"
	curl "http://$1:$NAGIOS_PORT/objects" -sS --connect-timeout $CONNECTION_TIMEOUT --max-time $MAX_TIME > $filename
	mv $filename /tmp/$1
}
function get_cache {
	touch /tmp/datefile
	for server in "${NAGIOS_LIST[@]}"
	do
		get_server $server
	done
}
function get_date {
	echo $(date -r $1 +"%Y%m%d")
}
function updatecache {
	if [ ! -f /tmp/datefile ]
	then
		get_cache
	else
		yesterdate=$(date --date="yesterday" +"%Y%m%d")
		last_cache=$(get_date /tmp/datefile)
		if [ $yesterdate -gt $last_cache ]
		then
			get_cache
		fi
	fi
}
function test_server {
	nagios=$1
	hostname=$2
	if [ ! -f /tmp/$nagios ]; then
		get_cache
	fi
	state=$(cat /tmp/$nagios)
	count=$(echo $state | grep -o "\"$hostname\"" | wc -l)
	echo $count
}
function do_server {
	nagios_server=$1
	hostname=$2
	if [ $(test_server $nagios_server $hostname) -gt 0 ]
	then
		if [ "$4" == "true" ]
		then
			hours=$3
			let time=($hours*3600)
			comment_json="{\"host\": \"$hostname\", \"comment\": \"Jobname: $RD_JOB_NAME, Duration: $hours hour(s), Username: $RD_JOB_USERNAME, URL: $RD_JOB_URL\"}"
			url="http://$nagios_server:$NAGIOS_PORT/add_comment"
			echo "Putting $hostname on $nagios_server to downtime for $hours hour(s)"
			result=$(json_post "$comment_json" $url)
			if [ $result -gt 0 ]
			then
				echo "Comment set successfully"
			else
				echo "Failed to set comment for $hostname on $nagios_server"
			fi
			result=$(json_post "{\"host\": \"$hostname\", \"duration\": $time}" http://$nagios_server:$NAGIOS_PORT/schedule_downtime)
			if [ $result -gt 0 ]
			then
				echo "$hostname in downtime"
			else
				echo "Unable to put $hostname in downtime, should have been accessible on $nagios_server"
				exit 2
			fi
		else
			echo "Waiting..."
			sleep 10
			echo "Pulling $hostname on $nagios_server out of downtime"
			result=$(json_post "{\"host\": \"$hostname\", \"comment\": \"Pulling $hostname out of downtime early\" }"  http://$nagios_server:$NAGIOS_PORT/add_comment)
			if [ $result -gt 0 ]
			then
				echo "Comment set successfully"
			else
				echo "Failed to set comment for $hostname on $nagios_server"
			fi
			result=$(json_post "{\"host\": \"$hostname\"}" http://$nagios_server:$NAGIOS_PORT/cancel_downtime)
			if [ $result -gt 0 ]
			then
				echo "$hostname out of downtime"
			else
				echo "Unable to pull $hostname from downtime, should have been accessible on $nagios_server"
				exit 2
			fi
		fi
		exit 0
	fi
}

# edited by hectorp
# instead of extracting from the begining until the first dot,
# now removes everything after the second to last dot.

fullname=$2
hostname2=${fullname%.*}
hostname=${hostname2%.*}
colorprint $CYAN "Sending downtime to $hostname"
hours=$1
mode=$3

updatecache
for server in "${NAGIOS_LIST[@]}"
do
	do_server $server $hostname $hours $mode
done
echo "WARNING: Downtime not set - $hostname not found on any nagios server"