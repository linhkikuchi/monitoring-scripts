# run /usr/local/bin/check_search_result.sh $HOSTADDRESS$

E_SUCCESS="0"
E_CRITICAL="2"


status=`curl -L -s -o /dev/null -w "%{http_code}" "http://$1/search?w=*&log=no&sli_jump=1"`

if [ "$status" == "200" ] ; then
	echo "Search OK"
    exit ${E_SUCCESS}
else
        echo "Search didn't return 200. Please check!"
        exit ${E_CRITICAL}
fi
