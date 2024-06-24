# How to use the /data directory

Since we are producing, using and sharing a lot of configuration data, we share them in this directory.
The structure is as follows:

- `devices`: Please put files related to a specific chip into a subdirectory e.g. `fc8a` for the design with tha name

If we are coming up with any other kind of data that we want to share, we can have a new folder for it.

When uploading data, make sure to:

- **Do not commit overly large data such as logs or big images**
- **Do not commit raw or unprocessed data**
- Instead, please commit only useful information in readable commonly used formats such as:
  - Mixer correction in csv format
  - Device configuration toml files