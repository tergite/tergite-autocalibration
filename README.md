# README #
This project contains an orchistration manager, a collection of callibration schedules and a collection of post-processing & analysis routines.  
It is tailored for the tune-up of the 25 qubits QPU at Chalmers, QTL.  
This repository utilizes **`redis`** for on memory data storage.  
As redis operates only on Linux systems, this repo can only work either on Linux distributions or WSL (Windows Subsystem for Linux) environments, installed on a Windows system.  
To install WSL, it is required **Windows 10** of version at least **1903**.

## Repository installation:
After setting up your ssh key, clone the repo:
```git clone```

### Create your local environment ###
```Conda create```

### Install the required packages from the requirements.txt file ###
```ip install req```

### Install the repository in editable mode so all your changes are applied whithout the need of reinstall ###
```pip install -e .```

## Operation: ##
To delete all redis entries:  
```python resetredis.py all```  
To reset a particular node:  
```python resettedis <nodename>```  
**To start a new calibration sequence according to the configuration files:**  
**```python worker/calibration supervisor```**  

## Configuration files
`utilities/user_input.py`  
`configuration_files/hardware_configuration.py`  
`configuration_files/transmon_element.toml`  

## Structure
Compilation execution post processing  

## Data browsing
Datasets are stored in data directory
Can be viewed with dataset viewer
