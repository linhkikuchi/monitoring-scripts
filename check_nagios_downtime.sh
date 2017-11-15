# This nagios plugin checks to see the nagios downtime port is open and responding
#

E_SUCCESS="0"
E_CRITICAL="2"
server="server-name"
port="6315"

status=`curl -sH "Content-Type:application/json" "http://$server:$port/add_comment" -d "{\"host\": \"test-host\", \"comment\": \"Jobname: test, Duration: 1hour(s), Username: test_only, URL: N/A\"}"`

if [ $? -ne 0 ]; then
        echo "Nagios Downtime is not responding"
        exit ${E_CRITICAL}
else
        echo "Ok - Nagios Downtime is responding"
        exit ${E_SUCCESS}
fi
