# greppy
[![Package Status](https://img.shields.io/badge/status-experimental-yellow)](https://github.com/psteitz/greppy)
[![License](https://img.shields.io/badge/license-apache2-green)](https://github.com/psteitz/greppy/blob/main/LICENSE)

## What is this?
Greppy is a little command line utility for filtering csv files that dreams of one day becoming a real application.
## Main Features
Greppy does only one thing, which is to filter input csv files for records that match search criteria.
Under the covers, greppy generates and uses awk scripts to do the filtering.  It saves the scripts that it generates,
so it can also be used as an awk script generator for csv filters. Because greppy does not load anything more than a 
single line into memory at a time, it can handle very large files.
## Dependencies
Greppy has no Python dependencies, but it uses awk. For it to run, both python (version 3) and awk must be installed locally and on the system path when it is launched on the command line. Greppy prefers to use gawk, but the scripts that it generates do not use any gawk extensions.
## Documentation
### Installing greppy
 1. Make sure that python 3 and awk are installed and on the system path.  Enter ```python3 --version``` and ```awk --version``` to verify. Even ancient versions of awk will work, but it is better to install gawk. The easiest way to install gawk on apt-friendly Linux systems is to just ```sudo apt install gawk```.  On MacOS, homebrew should work.  For windows, follow the directions [here](https://gnuwin32.sourceforge.net/packages/gawk.htm) to download gawk.  Run ```setup.exe``` from the download site, taking the defaults for installation locations.  Then you need to get the gnu binaries onto the Windows system path.  To do that, follow the instructions [here](https://www.mathworks.com/matlabcentral/answers/94933-how-do-i-edit-my-system-path-in-windows). The path you want to navigate to and add is ```C:\Program Files (x86)\GnuWin32\bin\```.  Python is easier to install.  Just type ```python3``` on the command line and if it is not installed already it will ask you if you want to get it from the Windows app store.  Say yes and it will be installed.  
 2. Clone this repo or just download the file greppy/runner/greppy.py
### Greppy "programs" 
One day, if he is a good boy, greppy will get a UI so users can provide search criteria easily.  For now, he is still just a wooden puppet, so you have to provide search criteria and input file specifications in little text files that tell greppy what to do.  The best way to understand the format of these files is to look at the examples in the /examples directory of this repo.  

It's probably best to just imitate the examples and experiment with small files to learn how greppy programs work, but here is a little more info on how greppy thinks. It is OK and maybe even recommended to skip this until you have looked at the examples.

Lines that start with '#' are ignored by greppy, but they are good for explaining what (you think) you are asking greppy to do.

The first (non-comment) line of a greppy program _must_ be a file specification of some kind.  It can specify a directory and it can use relative paths, but these must be relative  to the location where greppy.py is installed.  It is in general best to use full paths.  It can be a network share, like ```\\san-01\foo\incoming``` or the full path to a file, like ```/home/billybob/coolio.csv```.  It has to be a file spec that the OS that greppy is running on can understand and greppy has to have access to the directory or file.

After the file spec, anywhere in the file, there can be _directive_ lines:
  * !FIELDS [field1, field2. ..., fieldn] - names of the fields.
  * !SEPARATOR ,
  * !NO_HEADER - if present, assume the csv has no header. Ignore !FIELDS and allow only $ column references in match rules

If there are no directives in the program, Greppy assumes that the first line in the input csv files is a header line containing field names (standard setup for csv files). The !FIELDS lists don't have to include all of the fields, but they must be in the right order and include all fields between the first and last on the list. 

!SEPARATOR lines over-ride the default "|" column separator.  So if the file uses commas as separators, use ```!Separator ,``` .

Following the file spec and directive lines above, there _may_ be a line with just the word, 'NOT', in which case everything that follows is negated.  In other words, we are asking greppy to return all lines that do NOT satisfy the conditions to follow.

The following lines can include exactly one 'AND' or 'OR' line and that must be the first line after 'NOT' if there is a 'NOT,'

Other lines express _match clause_ filtering criteria or awk-language match conditions.

_Match clauses_ assert relationships between a match field value and a target. If there is an OR or AND in front of them, they are combined in the natural way and there can be any number of them. 

Match clause lines have up to three |-delimited parts. For example, 
 * NOT | productId | 27 
 * price | > 100

If there are three parts, the first one must be 'NOT'.  Following the optional NOT, match clauses have a target field and a comparison target expression.  The target field can be a column name (read from the header or defined in a !FIELDS directive) or a ```$i``` reference, where ```i``` is an integer between 0 and the number of fields (inclusive).  

The first example above asserts that the productId field does not equal 27.  The second one says the value in the price column has to be greater than 100.

Here are some more examples:

 * $2 | 27 
 * $13 | >= $18
 * $12 | $price + $cost

If target expressions start with comparision operators (like ```>=```), the match clause asserts that comparison between the target field and the target expression.  If there is no comparison operator, the match clause asserts that the target field equals the target expression.

The first example above says that the value in the second column equals 27.  The second one says that the value in column 13 is at least as big as cthe value in olumn 18.  The last one says that the 12th column is the sum of spice and cost. 

Note that greppy column references are 1-based, so for example $1 refers to the first column. Greppy is a native awk-speaker, so he sees $0 as the full input line, which won't work in greppy as either a target field or as part of a target expression. Matches using $0 will always fail.

If the target expression is a list of values in brakets, separated by commas, the match succeds if the match field exaclty matches one of the values. The 'NOT' in the first field, if there is one, does the natural thing.

Target expressions can assert that the target field has the target expression as a substring by surronding the substring with /'s.  For example,

```productName | /crumpets/```

This match clause asserts that the value in the productName column includes 'crumpets' as a substring.

Any regular expression using any defined field names or column references can be put between the /'s above. 

Here are some examples:
 * ```NOT | ProductId | /12/``` means ProductId can't contain '12' in it.  So records with ProductId equal to '212', '12', '1233' will not match, 
 * ```SalesPrice | >= 10``` matches all records where the value of the SalesPrice field is at least 10.
 
 When target values don't have comparison operators and aren't surrounded by /'s, they mean exact match, but the comparison ignores leading and trailing spaces and quotes.  

 * ```ProductName | salt peanuts``` will match csv lines with '   salt peanuts  ', '  "salt peanuts"' or even '"salt peanuts' in the ProductName column. but not 'salt peanuts 2'.  If there is only one field in a greppy program line, greppy looks for the match in any field.

Here is a detailed explanation for the example program called ```greppy_multi_file.txt``` in the examples folder:
<pre>
C:\users\billybob\downloads\
NOT
OR
ProductId | [1123, 2234, 1111]
ProductDescription | /crumpets/
</pre>
The first line points greppy at all of the csv's files in billybob's downloads folder.  This obviously will only work on Windows likely for only billybob himself.
The NOT at the beginning says all that follows is to be negated.  The OR means any one of the following matches needs to succeed. The ProductId match looks for matches on ProductId against any of 1123, 2234, 1111 and the ProductDescription match looks for 'crumpets' contained in that field.  So what we are looking for all together is records that do not have product ids 1123, 2234, 1111 and do not have 'crumpets' somewhere in their description.  So assuming that ProductId if we have a csv like
<pre>
ProductId | ProductDescription
1123 | tea and crumpets
1124 | fish tacos
2234 | cheerios
2222 | fancy crumpets
9999 | apples
</pre>
when run with this program, greppy will return
<pre>
ProductId | ProductDescription
1124 | fish tacos
9999 | apples
</pre>
 
### awk match condtions
Greppy progam lines that start with 'awk' are assumed to be awk match conditions. These work like the match_clauses above.  They are combined using the AND and OR that may be defined above them and any other awk or match_clauses that preceede them. Any awk match expression can be used. Column names, if they appear, are replaced by field indexes.


### Running greppy
Type ```python3 greppy.py prog.txt``` where ```prog.txt``` is a greppy program file.  If the program file is not in the same directory that you launch greppy from, you need to provide the full path to that file.  Greppy streams its output to the console and also creates an output ```.csv``` file in the directory where ```greppy.py``` is
located.  It also creates a ```.awk``` file in that directory.  The names of these files are a kind of ugly combination of the name of the program file and the input csv. 
If the first line of the program file specifies a directory, greppy filters all of the .csv files in that directory. Results are written to the console sequentially and
combined into a single output csv.  Greppy assumes that input csv are pipe-delimited, i.e., the column separator is ```|```.  One day that will be configurable.
### Troubleshooting 
