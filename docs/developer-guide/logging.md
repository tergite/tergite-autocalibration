# Logging

This page is about logging and will guide through a couple of questions such as:

- How do logs end up in the console and in the log file?
- Where are logs stored?
- How is the logger used inside the code?
- What logging levels are there?

Logging is a minor aspect of the application, but if there is some consistency in the way logs are handled, it can make the debugging much faster.

## General logging to console and file
In Python there are several ways to log messages.
The easiest one is probably to put a `print()` statement into the code and see the outcome in the console.
There are a couple of way such as `sys.stdout.write()` to do logging closer to the system.
Finally, a very sophisticated way to do logging is offered with the built-in [`logging`](https://docs.python.org/3/library/logging.html) module.

With the `logging` package, it is easy to register an own logger class and to implement functionalities such as logging to the console and a file at the same time.
Also, the `logging` package offers levels to prioritize messages in the logging.
With these levels it is possible to have a very high verbosity in the logging during development and only show critical errors or warning during production.
More about levels below in the [section about logging levels](#logging-levels).

In the automatic calibration, there is an extended version of the logger in the `logging` package.
It can be found in `utils/logging/__init__.py`.
When you want to use the logger inside the code, you will have to import the logger:

```python
from tergite_autocalibration.utils.logging import logger

logger.info("Hello world")
```
This will create the logger and print a message on the info level.

## Logging levels
The logging package offers different levels such as `notset=0` `debug=10`, `info=20`, `warning=30`, `error=40`, and `critical=50`.
If the level is set to e.g. 30, all messages with a lower logging level such as `debug` or `info` will be suppressed.

When you are having a lot of external packages such as `qcodes`, they might log a lot of messages on the `info` level, which are still very detailed.
This is why the autocalibration has a level itself, which is on 25 and called `status`.
Here, you can see how this looks in practice:
```python
from tergite_autocalibration.utils.logging import logger

logger.warning("This is a very important log message") # level: 30
logger.status("This is an important log message")      # level: 25
logger.info("This is a less important log message")    # level: 20
```

As a rule of thumb, use `logger.status()` for important messages such as there is a node to be calibrated.
Use the `logger.info()` for less important messages such as printing the fit result of an analysis function.
In case you want to print very low level messages, such as raw results or indications where you enter a function while debugging, please use `logger.debug()`.
And for warnings and errors, use the respective log levels.

You can set different log levels for the console and file output by setting the environmental variables  in the `.env` file.
```bash
STDOUT_LOG_LEVEL='25'
FILE_LOG_LEVEL='10'
```
These values above are the default.
The effect will be that the application will write a very detailed log to the log file.
In the console prints, there will be only status, warning and error messages.

## Log directories
The logs are stored in a directory that is defined by the data directory in the environment variable `DATA_DIR`.
Usually, there should be no need to define the `DATA_DIR` variable as the application will automatically create a folder called `/out` on the root level of the repository.
Inside the data directory there will be created a folder for each day in the format `YYY-MM-DD` when one starts a measurement.

For each run of the calibration or other command, there is going to be created another subfolder inside the folder of the day.
This folder follows the pattern `HH-MM-SS_STATUS-node_name` meaning that is starts with a timestamp, followed by the application status and the node, which is the target to calibrate.
For the status there are the following options:

- `ACTIVE`: While your script is running, this indicates that inside the folder, there will be active read and write operations.
- `SUCCESS`: In case the calibration terminated successfully. This does not mean that it has found the right calibration values. It just means that it did not crash at some point in between.
- `FAILED`: In case there was an error.

These folder names are changing automatically while the application is running or shutting down, so, please do not change the folder names manually during a calibration.

### Special log locations
There are two special occasions when logs are taken that do not fall into the categories above.

The first of them is the **default** folder.
This folder is used for all logs where the application is used either the first time or when the application is in a state without any configuration.
The default log will just be appended and create one long log file.

Logs can also be intentionally routed to the default log directory by adding a `suppress_logging` decorator to a commandline endpoint.
This should be added below the typer command decorator.
```python
import typer
from tergite_autocalibration.utils.logging.decorators import suppress_logging

my_typer_cli = typer.Typer()

@my_typer_cli.command(help="Example command")
@suppress_logging
def endpoint():
    """Endpoint for the cli"""
    pass
```
Please note that this method is only meant to route logging within typer endpoints.
If you want to change the verbosity of your logs, please read the section above.

The other special folder to save logs is the **pytest** folder.
It contains the logs from running the unit tests.
