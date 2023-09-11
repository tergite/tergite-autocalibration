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

#### Create your local environment.   ####
For example, here the environment is named `tac`  
```conda create --name tac python=3.9```  
```conda activate tac```

#### Enter the project root directory:  ####
```cd tergite-autocalibration-lite/```  
**From now on, it is assumed that all commands are executed from the project root directory.**


#### Install the required packages from the requirements.txt file ####
```pip install -r requirements.txt```

#### Install the repository in editable mode so all your changes are applied whithout the need of reinstall ####
Here `.` is the current directory (i.e. the directory that contains the `setup.py` file)  
```pip install -e .```

## Operation: ##
To delete all redis entries:  
```python reset_redis.py all``` 

To reset a particular node:  
```python reset_redis.py <nodename>```  

For example to reset the node `rabi_oscillations`:  
```python reset_redis.py rabi_oscillations```

**To start a new calibration sequence according to the configuration files:**  
**```python workers/calibration_supervisor.py```**

## Configuration files
The sample-space for each node. Also here the target node is declared:  
`utilities/user_input.py`  

Qblox Cluster configuration file:  
`config_files/settings.py`  

A collection of reasonable initial values for the device:  
`config_files/device_config.toml`  

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