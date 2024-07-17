#!/bin/bash

# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#
# This code is a modification of the blog post found here:
# https://gist.github.com/inecmc/f40ca0ee622e86999d9aa016c1b15e8c


if [ "$EUID" -eq 0 ] || [ -n "$SUDO_USER" ]; then
    echo "Reading input arguments..."
else
    echo "Removing a redis instance is only possible with sudo rights."
    echo "Please restart the script as root user or with sudo."
    exit 1
fi

REDIS_USER_VARIABLE=""
REDIS_USER_PORT=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --name)
            REDIS_USER_VARIABLE="$2"
            shift 2
            ;;
        --port)
            REDIS_USER_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument passed: $1, please pass --name and --port arguments."
            exit 1
            ;;
    esac
done

if [ -z "$REDIS_USER_VARIABLE" ] || [ -z "$REDIS_USER_PORT" ]; then
    echo "Please pass --name and --port arguments to properly remove the redis storage instance."
    exit 1
fi

if [ "$REDIS_USER_PORT" == "6379" ]; then
    echo "This script is not intended to uninstall the default redis server running on port 6379."
    echo "To uninstall redis completely, please visit the official redis documentation."
    exit 1
fi

# Output the values
echo "--------------------------------------------------------------------"
echo "Removing redis storage configuration with name: $REDIS_USER_VARIABLE"
echo "Running on port:                                $REDIS_USER_PORT"
echo "--------------------------------------------------------------------"

# Checking the port
echo "Checking whether installation can be removed..."

if ps aux | grep -qE "redis-server.*:$REDIS_USER_PORT"; then
    echo "Redis instance found for port $REDIS_USER_PORT."
else
    echo "No redis instance found for port $REDIS_USER_PORT."
    exit 1
fi

if [ -f "/etc/redis/redis_$REDIS_USER_VARIABLE.conf" ]; then
    echo "Redis instance connected to user $REDIS_USER_VARIABLE."
else
    echo "The redis instance on port $REDIS_USER_PORT is not connected to the --name argument."
    echo "Abort removing process."
fi

# Ask again whether to continue to remove the redis instance
echo "Do you want to continue and remove redis instance $REDIS_USER_VARIABLE on port $REDIS_USER_PORT? (y/n)"
read -r continue_remove

# Loop until a valid response is provided
while [[ ! $continue_remove =~ ^[YyNn]$ ]]; do
    echo "Invalid input. Please enter (y) to continue or (n) to abort."
    read -r continue_remove
done

# Check the final continue_remove
if [[ $continue_remove =~ ^[Yy]$ ]]; then
    echo "Continuing removal..."
else
    echo "Aborting removal."
    exit 1
fi


# Find the PID of the redis instance to kill the server
pid=$(ps -eo pid,args | grep ":$REDIS_USER_PORT" | awk 'NR==1 {print $1}')
kill -9 "$pid"

# Stop, disable and mask the service
systemctl stop "redis-server-$REDIS_USER_VARIABLE.service"
systemctl disable "redis-server-$REDIS_USER_VARIABLE.service"
systemctl mask "redis-server-$REDIS_USER_VARIABLE.service"
systemctl daemon-reload

systemctl status "redis-server-$REDIS_USER_VARIABLE.service"


rm "/etc/redis/redis_$REDIS_USER_VARIABLE.conf"
rm "/lib/systemd/system/redis-server-$REDIS_USER_VARIABLE.service"

echo ""
echo "Redis storage removed for $REDIS_USER_VARIABLE on port $REDIS_USER_PORT."