# Greppy examples
The examples in this directory illustrate the different kinds of things that greppy "programs" can do.
The easiest way to run greppy is to execute ```python3 greppy.py file_name``` with ```file_name``` the name of
a greppy program file in the same directory where greppy.py is installed. The examples here are all example programs.

## Using greppy to find records that have a certain value in a specific column
The example, [```greppy_column.search.txt```](https://github.com/psteitz/greppy/blob/main/examples/greppy_column.search.txt), shows how to filter records to those having
 ```productId``` equal to ```13455```.  The first non-comment line of the file ```test.csv``` specifies the input file
 to look for records in.  Since there is no path specification in front of the name, greppy will look for the file
 in the same directory where the program is.  If you are just searching one file, the easiest way to do it is to
 copy the file and the program to the same directory where greppy is installed; otherwise you need to provide the
 full path to the file.

 
## Combining conditions on column values using ```OR, AND, NOT```
Each line of a greppy program makes an assertion about field values.  These assertions can be combined using ```OR```
(records satisfying at least one condition get included) or ```AND``` (records need to satisfy all conditions).  A single
```NOT``` line can be used to mean that you want all records that do not meet the combined conditions.
The file, [```greppy_and.txt```](https://github.com/psteitz/greppy/blob/main/examples/greppy_and.txt) shows how to combine
match conditions.  The ```AND``` line at the top means that the conditions on the following lines must all be satisfied
for records to be returned.  The line, ```ProductDescription | /nut/``` says that the ProductDescription column must contain
the string 'nut'.  The /'s surrounding 'nut' mean that it does not have to be an exact match - just 'nut' is in the value
somewhere, so for example 'peanut', 'nut case' and 'apple nut cake' would all match.  Actually, you can put any regular expression
between /'s to use it as a column match condition.  The next line, ```NOT | ProductCategory | snacks``` says that the ProductCategory
is not snacks.  Putting it all together, this program returns all records where the ProductDesctiption contains the string 'nut'
and the ProductCategory is not (exactly) equal to 'snacks'.  Greppy ignores leading and traling spaces in programs and input
csv's, so ' snacks', ' snacks ', and 'snacks' in the column will all match.

The examples we have seen so far assume that the input file has a header record including the column names.  If those are missing, 
you can provide them using the ```!FIELDS``` directive.  The file, [```greppy_and_no_header.txt```](https://github.com/psteitz/greppy/blob/main/examples/greppy_and_no_header.txt) shows how to specify column names when they are missing from the input file.

## Selecting records where a column falls within a specified range of values
The example, [```greppy_range.txt```](https://github.com/psteitz/greppy/blob/main/examples/greppy_range.txt), shows how to select records where the ```Price``` column falls within the range between ```2``` (inclusive) to ```5``` (exclusive). The line, ```Price | >= 2``` specifies the condition that the ```Price``` column must be greater than or equal to ```2``` and the following line says it must be stricly less than  ```5```. The ```AND``` at the beginning says that both of the conditions that follow must be true.

## Providing header column names for files that do not have them on the first line
The file, [```greppy_and_no_header.txt```](https://github.com/psteitz/greppy/blob/main/examples/greppy_and_no_header.txt) shows how to specify column names when they are missing from the input file. The "directive" line, ```!FIELDS [ProductId, ProductPrice, ProductDescription, ProductCategory]``` tells greppy that the input file does not have a header line and the first 4 columns should be named as above.

## Using column numbers instead of column names
You can use column numbers instead of column names anywhere in Greppy programs by putting a ```$``` in front of a number. The number has to be at least 1 and less than or equal to the number of columns in the file. You can mix and match $ column references with column names taken from headers or !FIELDS directives.
