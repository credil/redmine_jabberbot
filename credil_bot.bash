#!/usr/bin/env bash

START=$(date +%s.%N)

#exit when command fails (use || true when a command can fail)
set -o errexit

#exit when your script tries to use undeclared variables
set -o nounset

# in scripts to catch mysqldump fails
set -o pipefail

# Set magic variables for current file & dir
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # Dir of the script
__root="$(cd "$(dirname "${__dir}")" && pwd)"           # Dir of the dir of the script
__file="${__dir}/$(basename "${BASH_SOURCE[0]}")"       # Full path of the script
__base="$(basename ${__file})"                          # Name of the script
ts=`date +'%Y%m%d-%H%M%S'`

#Set the config file
configFile="$HOME/.binJlam/templateConfig"

#Capture everything to log
mkdir -p ~/log
log=~/log/$__base-${ts}.log
exec >  >(tee -a $log)
exec 2> >(tee -a $log >&2)
touch $log
chmod 600 $log

#=== BEGIN Unique instance ============================================
#Ensure only one copy is running
pidfile=$HOME/.${__base}.pid
# if [ -f ${pidfile} ]; then
#    #verify if the process is actually still running under this pid
#    oldpid=`cat ${pidfile}`
#    result=`ps -ef | grep ${oldpid} | grep ${__base} || true`

#    if [ -n "${result}" ]; then
#      echo "Script already running! Exiting"
#      exit 255
#    fi
# fi

set -x
if [[ `/bin/ps -ef | grep credil_bot.py | grep -v grep | grep -v vi | wc -l` != "0" ]]; then
      echo "Script already running! Exiting"
      exit 255
fi
set +x

#grab pid of this process and update the pid file with it
pid=`ps -ef | grep ${__base} | grep -v 'vi ' | head -n1 |  awk ' {print $2;} '`
echo ${pid} > ${pidfile}

# Create trap for lock file in case it fails
# trap "rm -f $pidfile" INT QUIT TERM EXIT
#=== END Unique instance ============================================



#Check that the config file exists
#if [[ ! -f "$configFile" ]] ; then
#        echo "I need a file at $configFile with ..."
#        exit 1
#fi

export DISPLAY=:0

echo Begin `date`  .....

echo; echo; echo;

### BEGIN SCRIPT ###############################################################

#(a.k.a set -x) to trace what gets executed
#set -o xtrace

screen -d -m -S credil_bot  $__dir/credil_bot.py

set +x

### END SCIPT ##################################################################

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo; echo; echo;
echo Done.  `date` - $DIFF seconds

#=== BEGIN Unique instance ============================================
# if [ -f ${pidfile} ]; then
#     rm ${pidfile}
# fi
#=== END Unique instance ============================================
