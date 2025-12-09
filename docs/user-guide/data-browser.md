# Data browser

The data browser enables you to inspect your plots and measured data in the web browser.

## Starting and stopping the browser

You can simply start the data browser by typing:

```
acli browser start
```

This will start the browser in the background on the address [http://127.0.0.1:8179](http://127.0.0.01:8179).
You can configure the location to start the data browser in the `.env` file.

```
DATA_BROWSER_HOST='127.0.0.1'
DATA_BROWSER_PORT='8179'
```

In a multi-user environment, please make sure to choose a free port.
We recommend for the last two digits to choose the same number as for your redis server.
I.e. if you redis instance is running on port 6384, you should run the data browser on 8184 to avoid port conflicts.

The data browser will run in the background until you stop it with:

```
acli browser stop
```