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

# Check whether the script is running with sudo privileges
if [ "$EUID" -eq 0 ] || [ -n "$SUDO_USER" ]; then
    echo "Reading input arguments..."
else
    echo "Creating a redis instance is only possible with sudo rights."
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
    echo "Please pass --name and --port arguments for the redis configuration."
    exit 1
fi

if [ "$REDIS_USER_PORT" == "6379" ]; then
    echo "Please choose another port than the default port 6379 for the default redis configuration."
    exit 1
fi

# Output the values
echo "--------------------------------------------------------------------"
echo "Creating redis storage configuration with name: $REDIS_USER_VARIABLE"
echo "Running on port:                                $REDIS_USER_PORT"
echo "--------------------------------------------------------------------"

echo ""

# Checking the port
echo "Checking whether port is in use..."

if ss -tuln | grep -q ":$REDIS_USER_PORT"; then
    echo "Port $REDIS_USER_PORT is in use, please select another port."
    exit 1
else
    echo "Port $REDIS_USER_PORT is free."
fi

echo ""


# Create the directory for the new instance
install -o redis -g redis -d "/var/lib/redis_$REDIS_USER_VARIABLE"


echo "Writing configuration..."
# Create a temporary configuration file
TEMP_CONF_FILE="redis_$REDIS_USER_VARIABLE.conf"
# Replace the ports and user names
sed -e "s/REDIS_USER_VARIABLE/$REDIS_USER_VARIABLE/g" \
    -e "s/REDIS_USER_PORT/$REDIS_USER_PORT/g" \
    redis_template.conf > "$TEMP_CONF_FILE"

# Copy the adjusted file to the system location
cp "$TEMP_CONF_FILE" "/etc/redis/redis_$REDIS_USER_VARIABLE.conf"
# Cleanup the temporary config file
rm "$TEMP_CONF_FILE"


echo "Writing service configuration..."
# Create a temporary service file
TEMP_SERVICE_FILE="redis-server-$REDIS_USER_VARIABLE.service"
# Replace the user names
sed "s/REDIS_USER_VARIABLE/$REDIS_USER_VARIABLE/g" redis-server-template.service > "$TEMP_SERVICE_FILE"
# Copy the service file
cp "$TEMP_SERVICE_FILE" "/lib/systemd/system/redis-server-$REDIS_USER_VARIABLE.service"
# Cleanup the temporary file
rm "$TEMP_SERVICE_FILE"

# Try to enable and start the service
systemctl unmask "redis-server-$REDIS_USER_VARIABLE.service"
systemctl enable "redis-server-$REDIS_USER_VARIABLE.service"
systemctl start "redis-server-$REDIS_USER_VARIABLE.service"
systemctl daemon-reload

echo ""
echo "Redis storage created for $REDIS_USER_VARIABLE on port $REDIS_USER_PORT."

systemctl status "redis-server-$REDIS_USER_VARIABLE.service"
