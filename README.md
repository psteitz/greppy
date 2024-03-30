# greppy
[![Package Status](https://img.shields.io/badge/status-experimental-yellow)](https://github.com/psteitz/greppy)
[![License](https://img.shields.io/badge/license-apache2-green)](https://github.com/psteitz/greppy/blob/main/LICENSE)

## What is this?
Greppy is a little command line utility that dreams of one day becoming a real application.
## Main Features
Greppy does only one thing, which is to filter input csv files for records that match search criteria.
Under the covers, greppy generates and uses awk scripts to do the filtering.  It saves the scripts that it generates,
so it can also be used as an awk script generator for csv filters.
## Dependencies
Greppy has no Python dependencies, but it uses awk. For it to run, both python (version 3) and awk must be installed locally and on the system path when it is launched on the command line. Greppy prefers to use gawk, but the scripts that it generates do not use any gawk extensions.
## Documnentation
### Innstalling greppy
 1. Make sure that python 3 and awk are installed and on the system path.  Enter ```python3 --version``` and ```awk --version``` to verify. Even ancient versions of awk will work, but it is better to install gawk. The easiest way to install gawk on apt-friendly Linux systems is to just ```sudo apt install gawk```.  On MacOS, homebrew should work.  For windows, follow the directions [here](https://gnuwin32.sourceforge.net/packages/gawk.htm).
 2. Clone this repo or just download the file greppy/runner/greppy.py
### Greppy "programs" 
One day, if he is a good boy, greppy will get a UI so users can provide search criteria easily.  For now, he is still just a wooden puppet, so you have to provide search criteria and input file specifications in little text files that tell greppy what to do.  The best way to understand the format of these files is to look at the examples in the /examples directory of this repo.  
### Running greppy
Type ```python3 greppy.py prog.txt``` where ```prog.txt``` is a greppy program file.  If the program file is not in the same directory that you launch greppy from, you need to provide the full path to that file.

If all goes well, greppy will display the filtered csv and also produce a prog.awk and prog.csv file where "prog" is the name of the program file (minus ".txt").
### Troubleshooting 
