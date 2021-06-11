# Aerial

Python package manager

# commands

 Command | argument |
 --- | --- | 
 **install** | `package name`
 **upload** | `package name`
 **info** | `package name`
 **all** |   *_*
 
 ## install
 Installs the specified package into a `packages/` folder in the same directory. The script will create the `packages` folder if it does not already exist
 
 ## upload
 Zips everything in the same folder and upload it under the specified `package name`. it will also ask for version and any dependencies to be listed *(dependencies are not automatically installed right now)*
 
 ## info
 Displays name, description, version, and dependencies of the specified package name if it exists on the server
 
 ## all
 Displays all avaliable packages on the server
