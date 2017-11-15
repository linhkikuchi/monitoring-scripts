#!/bin/bash

# read in the options, to be passed in via Nagios 'command_line'
while getopts d:t:a:h:s:l:o:w:m:u:n:e: option
do
  case "${option}"
    in
      d) SERVICEDESC=${OPTARG};;
      t) NOTIFICATIONTYPE=${OPTARG};;
      a) HOSTALIAS=${OPTARG};;
      h) HOSTADDRESS=${OPTARG};;
      s) SERVICESTATE=${OPTARG};;
      l) LONGDATETIME=${OPTARG};;
      o) SERVICEOUTPUT=${OPTARG};;
      w) NOTIFICATIONAUTHOR=${OPTARG};;
      m) NOTIFICATIONCOMMENT=${OPTARG};;
      u) USER5=${OPTARG};;
      n) HNAME=${OPTARG};;
      e) CONTACTEMAIL=${OPTARG};;
  esac
done

# compose original message, escaping % because it's reserved for printf
SERVICEOUTPUT=${SERVICEOUTPUT//%/%%}
message=$(printf "%s\n" "Notification Type: $NOTIFICATIONTYPE\n\nService: $SERVICEDESC\nHost: $HOSTALIAS\nAddress: $HOSTADDRESS\nState: $SERVICESTATE\n\nDate/Time: $LONGDATETIME\n\nAdditional Info:\n\n$SERVICEOUTPUT\n")

# craft different messages based on notification type
ack_info=""
if [ "${NOTIFICATIONTYPE,,}" = "recovery" ]; then
    subject="$NOTIFICATIONTYPE: $HOSTALIAS/$SERVICEDESC"

elif [ "${NOTIFICATIONTYPE,,}" = "acknowledgement" ]; then
    subject="ACKNOWLEDGEMENT: $HOSTALIAS/$SERVICEDESC"
    ack_info=$([[ ! -z $NOTIFICATIONAUTHOR ]] && printf "\nAcknowledged by: $NOTIFICATIONAUTHOR\nComment: $NOTIFICATIONCOMMENT\n")

else
    subject="** $NOTIFICATIONTYPE: $HOSTALIAS/$SERVICEDESC is $SERVICESTATE **"
    ack_link=`echo $SERVICEDESC | sed 's/\ /\+/g'`
    ack_info=$(printf "\nTo Acknowledge: $USER2?cmd_typ=34&host=$HNAME&service=$ack_link\n")
fi

#printf "ack_info" >> /tmp/mail.log

printf "$message$ack_info" | /bin/mail -s "$subject" $CONTACTEMAIL