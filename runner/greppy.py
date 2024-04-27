""" Greppy: A simple grep-like utility for searching csv files or directories of csvs."""

import argparse
import os
from pathlib import Path
import sys
from typing import Dict, Tuple
import subprocess


def parse_rules(config_file: str, fields: Dict[str, int]) -> str:
    """
        Parse the rules from the config file and return a match string to be used in the awk script.
        args:
            config_file: The name of the config file that contains the match rules.
            fields: A dictionary of field names and their index in the csv file.
        returns:
            A string that can be used in the awk script to match the records that meet the criteria.
    """
    order_operators = ['<', '>']
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        operator = ''
        components = []
        negate = False
        for line in lines:
            line = line.strip()
            if len(line) == 0 or line.startswith('#') or line.startswith('!'):
                continue  # Skip comment lines, blank lines and directives
            if line in ['OR', 'AND']:
                if line == 'OR':
                    operator = '||'
                else:
                    operator = '&&'
                continue
            if line == 'NOT':
                negate = True
                continue
            # this is a match line, split on | and check for NOT
            parts = line.split('|')
            clause_negate = False
            field = ""
            if len(parts) == 3:
                # First part must be NOT
                if parts[0].strip() != 'NOT':
                    print("Error parsing line: ", line)
                    raise ValueError("Error parsing line: " + line)
                field = parts[1].strip()
                clause_negate = True
                value_index = 2
            elif len(parts) == 2:
                # Next part is the field name
                field = parts[0].strip()
                value_index = 1
            else:
                value_index = 0
            # Get the value
            value = parts[value_index].strip()
            # Check if value is a list.  If so, generate a regex to match any value in the list.
            # Someting like this: '~//^[ ]*\"?(231|117|21|7)"?[ ]*$/'
            # ignoring leading and trailing spaces and optional quotes
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1].split(',')
                value = [v.strip() for v in value]
                value = '|'.join(value)
                value = f"/^[ ]*\"?({value})\"?[ ]*$/"

            # Add the clause to the components list
            components.append(
                (clause_negate, field, value))

    # Build the match string
    # First check to make sure that if there is more than one component, the operator is || or &&
    if len(components) > 2 and operator not in ['||', '&&']:
        print("Error: Multiple components require OR or AND")
        raise ValueError("Error: Multiple components require OR or AND")

    match = ""
    for i, component in enumerate(components):
        # Skip the first component, which comes from the first line in the config
        if i == 0:
            continue
        (neg, fld, val) = component
        # To ignore leading and trailing spaces and allowing optional quotes,
        # need to target a regex that looks like this: ^[ ]*["]?{val}["]?[ ]*$
        comparator = '!~' if neg else '~'
        if val.startswith('/'):  # Contains search
            match += f"${fields[fld]} {comparator} {val}"
        elif val[0] in order_operators:  # Order comparison, value includes the test
            match += f"${fields[fld]} {val}"
        else:  # Use regex to ignore leading and trailing spaces and optional quotes
            match += f"${fields[fld]} {comparator} /^[ ]*\"?{val}\"?[ ]*$/"
        if i < len(components) - 1:
            match += f" {operator} "
    if negate:
        match = f"!({match})"
    return match


def generate_awk_script(match: str, fields: Dict[str, int], field_separator="|", has_header=True) -> str:
    """
    Generate the awk script, using the match string.
        args:
            match: The match string generated from the rules in the config file.
            fields: A dictionary of field names and their index in the csv file.
            field_separator: The separator used in the csv file. Default is '|'.
        returns:
            A string that is the awk script that can be used to search the csv files.
    """
    # If input file has no headers, generate a header line from the fields dictionary
    # Also, match all lines in the file.
    if not has_header:
        header = field_separator.join(fields.keys())
        # Strip off the last field_separator
        header = header[:-1]
        awk_script = f'BEGIN {{ FS="{field_separator}"; print "{header}" }}\n'
        awk_script += f'{match}  {{ print $0 }}\n'
    else:
        # If input file has headers, print the first line and then match the rest of the lines.
        awk_script = f'BEGIN {{ FS="{field_separator}"}}\n'
        awk_script += 'NR == 1 { print $0 }\n'
        awk_script += f'NR > 1 && {match}  {{ print $0 }}\n'
    return awk_script


def get_file_spec(config_file: str) -> Tuple[str, str]:
    """Get the file or directory to be searched."""
    # Read the first line of config_file. See if it designates a directory or a file.
    # If it is a directory, return 'dir' and the directory name.
    # If it is a file, return 'file' and the file name.
    with open(config_file, 'r', encoding='utf-8') as f:
        # Skip blank lines and comments
        while True:
            first_line = f.readline().strip()
            if len(first_line) == 0 or first_line.startswith('#'):
                continue
            else:
                break
        if os.path.isdir(first_line):
            return 'dir', first_line
        return 'file', first_line


def get_fields(path: str, path_type: str, field_separator: str) -> dict:
    """ 
     Get the fields from the first line of the file_spec or the first csv file in the directory.
     Return a dictionary of field names and their index in the csv file.
     Add an empty string key with value 0 for full record match.
        args:
            path: The file or directory to be searched.
            path_type: 'dir' if path is a directory, 'file' if path is a file.
            field_separator: The separator used in the csv file.
        returns:
            A dictionary of field names and their index in the csv file.
     """
    if path_type == 'dir':
        file_list = [os.path.join(path, f) for f in os.listdir(path)]
        for file in file_list:
            if file.endswith('.csv'):
                with open(file, 'r', encoding='utf-8') as f:
                    fields = f.readline().strip().split(field_separator)
                    ret = {fields[i].strip(): i +
                           1 for i in range(len(fields))}
                    break
    else:
        with open(path, 'r', encoding='utf-8') as f:
            fields = f.readline().strip().split(field_separator)
            ret = {fields[i].strip(): i + 1 for i in range(len(fields))}
    # Add {"": 0} to the fields dictionary for full record match
    ret[""] = 0
    return ret


def process_directives(config_file: str) -> Tuple[str, dict]:
    """Process directives in the config file.
    args:
        config_file: The name of the config file that contains the match rules.
    returns:
        A tuple containing the field separator and a list of column names.
        If !FIELDS directive is found, the column names are taken from the directive, otherwise an empty list is returned.
        If !SEPARATOR directive is found, the field separator is taken from the directive, otherwise '|' is returned.
    """
    field_separator = '|'
    fields = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('!FIELDS'):
                # Strip off the "!FIELDS" directive
                line = line[7:].strip()
                # Strip the [] from the line and split on commas
                line = line[1:-1]
                field_list = line.split(',')
                fields = {name.strip(): i + 1 for i, name in enumerate(
                    field_list)}
                fields[""] = 0
            if line.startswith('!SEPARATOR'):
                field_separator = line.split(' ')[1].strip()
    return field_separator, fields


def main():
    """Main function."""
    # Parse command line arguments.  Expecting a single argument, the greppy match rules file, defaulting to greppy.txt
    parser = argparse.ArgumentParser(
        description='Greppy: A simple grep-like utility')
    parser.add_argument('config_file', nargs='?',
                        default='greppy.txt', help='Greppy configuration file')
    args = parser.parse_args()

    # Get the file spec from the config file and determine if it is a file or a directory
    path_type, file_spec = get_file_spec(args.config_file)

    # Process directives - !HEADER and !SEPARATOR
    field_separator, fields = process_directives(args.config_file)

    # Get the fields from the first line of the file_spec or the first csv file in the directory
    # if column names are not provided in directive.
    has_fields = len(fields) == 0  # has_fields means input files have headers
    if has_fields:
        fields = get_fields(file_spec, path_type, field_separator)

    # Parse the rules from the config file
    match = parse_rules(args.config_file, fields)

    # Generate a base output file name by contatenating the file_spec and rules file names with underscores
    # and removing special characters.
    output_name = file_spec + '_' + args.config_file
    output_name = output_name.replace('/', '_').replace(
        '.', '_').replace(' ', '_').replace('csv', '').replace('txt', '').replace('__', '_').replace('\\', '_').replace('C:', '').replace('-', '_')
    script_name = output_name + '.awk'

    # Generate and save the awk script
    awk_script = generate_awk_script(
        match, fields, field_separator, has_fields)

    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(awk_script)

    # Generate a list of files to process.  If the file_spec is a file, just process that file.
    # If it is a directory, add all files in the directory to the list.
    if path_type == 'dir':
        file_list = [os.path.join(file_spec, f) for f in os.listdir(file_spec)]
    else:
        file_list = [file_spec]

    # Execute the awk script on each file, printing the file name, then the results.
    # Also pipe the results to a file with the same name as the file_spec with a .csv extension.
    for _, file in enumerate(file_list):
        print(f"Results for {file}")
        sys.stdout.flush()
        p = Path(__file__).with_name(output_name + '.csv')
        with p.open('wb') as out:
            with subprocess.Popen(
                    ['gawk', '-f', script_name, file], stdout=subprocess.PIPE, text=True) as proc:
                for line in iter(lambda: proc.stdout.readline(1), ""):
                    sys.stdout.buffer.writelines([line.encode()])
                    out.writelines([line.encode()])
                sys.stdout.flush()
                sys.stderr.flush()
                out.flush()
                proc.wait()


if __name__ == '__main__':
    main()
