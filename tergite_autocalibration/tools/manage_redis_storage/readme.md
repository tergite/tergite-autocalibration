# Redis storage management

When using a shared environment on a Linux machine it can be an issue to have the same redis storage for all users.
This collection of shell scripts allows to manage the redis storage instances on a Linux machine.

**Tested for:** 
- Bash on Ubuntu 22.04
- Redis 7.2.5

## Usage
Before making any changes to redis storages, please check with the other users.

### List running redis instances
Run:
```
chmod +x list_redis_storage.sh
./list_redis_storage.sh
```
Here, `chmod +x` makes the script being executable if it was not already.
The output should be something like:
```
TODO: Add
```
This script is also working on MacOS.

### Create a new redis storage
Run:
```
chmod +x create_redis_storage.sh
sudo ./create_redis_storage.sh --name USERNAME --port PORT_NUMBER
```
Please replace `USERNAME` with your username and `PORT_NUMBER` with a free port under which you would like to reach the redis instance.
Here again, `chmod +x` is making the script being executable.
Please make sure to run the script with `sudo` rights, because it is changing some system services and needs to be elevated.

### Delete a redis storage given the port and username
Run:
```
chmod +x remove_redis_storage.sh
sudo ./remove_redis_storage.sh --name USERNAME --port PORT_NUMBER
```
Note: This will only remove redis storages created by the automatic script above.
You can find the port and username of a redis instance by using the `list_redis_storage.sh` script.

For Example:
```
TODO: Add example list and description what is user and port
```