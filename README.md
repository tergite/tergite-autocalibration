# README #
This project contains an orchistration manager, a collection of callibration schedules and a collection of post-processing & analysis routines.  
It is tailored for the tune-up of the 25 qubits QPU at Chalmers, QTL.  
This repository utilizes **`redis`** for on memory data storage.  
As redis operates only on Linux systems, this repo can only work either on Linux distributions or WSL (Windows Subsystem for Linux) environments, installed on a Windows system.  
To install WSL, it is required **Windows 10** of version at least **1903**.

## Repository installation: ##
#### After setting up your ssh key, clone the repo:  ####
```git clone git@bitbucket.org:qtlteam/tergite-autocalibration-lite.git```

#### Install Redis: ####
https://redis.io/docs/getting-started/installation/install-redis-on-linux/  

#### After installing redis, start the service, type from terminal: ####
```redis-server```  

#### Create your local environment.   ####
For example, here the environment is named `tac`  
```conda create --name tac python=3.9```  
#### Activate your local environment.   ####
```conda activate tac```

#### If you are not using conda, activate the environment with:   ####
```source activate tac```

#### Enter the project root directory:  ####
```cd tergite-autocalibration-lite/```  
**From now on, it is assumed that all commands are executed from the project root directory.**


#### Install the repository in editable mode so all your changes are applied whithout the need of reinstall ####
Here `.` is the current directory (i.e. the directory that contains the `setup.py` file)  
```pip install -e .```

Before operation please copy the variables from the `dot-env-template.txt` to a `.env` file and set the values according to the instructions in the template file:

```cp dot-env-template.txt .env```

You can edit the `.env` file with an editor of your choice such as `vim`, `nano` or any other text editor.

## Operation: ##
The package ships with a command line interface to solve some common tasks that appear quite often.

In the following there are a number of useful commands, but if you want to find out all commands use:
```acli --help```

To delete all redis entries:  
```acli node reset -a``` 

To reset a particular node:  
```acli node reset -n <nodename>```  

For example to reset the node `rabi_oscillations`:  
```acli node reset -n rabi_oscillations```

**To start a new calibration sequence according to the configuration files:**  
**```python tergite_acl/scripts/calibration_supervisor.py```**
or
**```acli calibration start```**

## Configuration files
The sample-space for each node. Also here the target node is declared:  
`tergite_acl/utils/user_input.py`

A collection of reasonable initial values for the device:  
`tergite_acl/config/device_config.toml`

The technical configuration parameters such as the path to the Qblox Cluster configuration file (including IP address) is documented in the `dot-env-template.txt`.

## Structure ##
For each calibration node:  
compilation -> execution -> post-processing -> redis updating

## Data browsing ##
Datasets are stored in `data_directory`  
Can be browsed with the dataset browser (coming soon)

## Development ##
When submitting  contributions, please prepend your commit messages with:
`fix:` for bug fixes  
`feat:` for introducing a new feature (e.g. a new measurement node or a new analysis class)  
`chore:` for refractoring changes or any change that doesn't affect the functionality of the code  
`docs:` for changes in the README, docstrings etc  
`test:` or `dev:` for testing or development changes (e.g. profiling scripts)  