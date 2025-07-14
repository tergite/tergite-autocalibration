# Troubleshooting

Some errors occur on more often than others.
If you are experiencing an error for which you find a simple hack that you want to share, please add it to this
troubleshooting guide.

As soon as the description for the hack is getting too long, we are going to add either a proper documentation page
about the topic or we just implement it as a feature.

### Redis

On a Linux machine, if REDIS does not accept a connection, you can do this:

```bash
redis-server --port {your redis port} --daemonize yes
```

The `--daemonize yes` parameter will enable the machine to run REDIS always in the background.
If you do not use that parameter, the REDIS instance will stop as soon as you close the terminal where you started it.

If you are getting an error saying:

```bash
15350:M 10 Dec 2024 23:24:17.172 # Warning: Could not create server TCP listening socket *:6379: bind: Address already in use
15350:M 10 Dec 2024 23:24:17.172 # Failed listening on port 6379 (tcp), aborting.
```

Then there might be already running a REDIS instance on that port.

You can verify that by typing:

```bash
redis-cli -p {the redis port you had the error with}
```

If it opens the REDIS CLI, then you have an instance already running.

To check whether there are already keys in the REDIS server - assuming you have opened the REDIS CLI - you can type:

```bash
keys *
```

This will give you all the keys that are stored in the REDIS instance.
If you are on a shared machine, you should always double-check whether no one else is using the same REDIS instance.
Otherwise, it could easily happen that you overwrite someone else's memory and data will be lost.

On Windows REDIS is run on WSL.
Kill the session and restart it and run REDIS (if you have not set it to run automatically).
Sometimes you may get in the situation that WSL will not open at all, in this case you need to restart the service
called “Hyper-V Host Compute Service”

### SPI

You can get an error saying that the default path was not correct or that you get denied permission.
Likely there was a connection implemented before and now when trying to start a new one it hangs itself up and refuses
communication, you can force this communication channel by running

```bash
sudo chmod 666 /dev/ttyACM0
```

### Concurrent operations
If two users access the same cluster at the same time, this message could be displayed

```bash
KeyError: 'The acquisition data retrieved from the hardware does not contain data for acquisition channel 0 (referred to by Qblox acquisition index 0).\n hardware_retrieved_acquisitions={}'
```

Contact the other users to avoid conflicts.