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

# Get the PIDs of all running redis-server instances
pids=$(pgrep -f redis-server)

if [ -z "$pids" ]; then
    echo "No running Redis instances found"
    exit 1
fi

echo "----------------------------------------------------------------------"

# Loop over the PIDs and create a table with ports and configurations
ports=()
for pid in $pids; do
    ports+=( "$(ps -p "$pid" -o args= | awk -F'[:]' '/redis-server/ {print $NF}')" )
done

echo "Redis instances are running on the following ports and configurations:"

for port in "${ports[@]}"; do
    pidfile=$(redis-cli -p "$port" CONFIG GET pidfile | awk 'NR==2 {print $0}')
    echo "$port :: $pidfile"
done

echo "----------------------------------------------------------------------"
