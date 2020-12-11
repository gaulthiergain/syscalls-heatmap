# syscalls-heatmap

This repository contains a python script to generate a syscalls
heatmap for Unikraft. An excel file which contains the current
syscalls status is provided in this repository.

# Installation

```
pip3 install numpy
pip3 install xlrd
pip3 install pandas
pip3 install seaborn 
pip3 install matplotlib
```
# Usage

```
python3 heatmap.py --help
usage: heatmap.py [-h] [--aggregated-file AGGREGATED_FILE] [--nb-apps NB_APPS]
                  [--folder-to-aggregate FOLDER_TO_AGGREGATE]
                  [--display-syscall-name [DISPLAY_SYSCALL_NAME]]
                  [--save-heatmap [SAVE_HEATMAP]]
```

There are two different modes:
1) **AGGREGATED_FILE**: Use the `--aggregated-file` argument following
by the path of a json file. This one contains an aggregated list of
syscalls that were gathered and aggregated by testing 30 applications.
The following file *"syscalls\_sample.json"* is provided as sample.
2) **FOLDER_TO_AGGREGATE**: Use the `--folder-to-aggregate` argument
following by the path of a folder that contains the json files
gathered by the [toolchain](https://github.com/gaulthiergain/tools).
These ones must use a particular structure that is defined by the
[toolchain](https://github.com/gaulthiergain/tools). An example folder
*"to\_aggregate"* is provided as sample.

Note that if you use the `--aggregated-file` argument, you need to 
adapt the `--nb-apps` argument. Its default value is 30.
