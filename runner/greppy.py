""" Greppy: A simple grep-like utility for searching csv files or directories of csvs."""

import argparse
import os
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
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        operator = ''
        components = []
        negate = False
        for line in lines:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue  # Skip comment lines and blank lines
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
            # Someting like this: '~/^(231|117|21|7) $/'
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1].split(',')
                value = [v.strip() for v in value]
                value = '|'.join(value)
                value = f"/^({value}) $/"

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
        else:  # Use regex to ignore leading and trailing spaces and optional quotes
            match += f"${fields[fld]} {comparator} /^[ ]*\"?{val}\"?[ ]*$/"
        if i < len(components) - 1:
            match += f" {operator} "
    if negate:
        match = f"!({match})"
    return match


def generate_awk_script(match: str, fields: Dict[str, int]) -> str:
    """
    Generate the awk script, using the match string.
        args:
            match: The match string generated from the rules in the config file.
            fields: A dictionary of field names and their index in the csv file.
        returns:
            A string that is the awk script that can be used to search the csv files.
    """
    # Generate the awk script.
    # In BEGIN block, Set the delimiter to | and print header line with field names.
    # For each line, if the line matches the match string, print the line.
    # Generate header line from fields dictionary
    header = '|'.join(fields.keys())
    awk_script = f'BEGIN {{ FS="|"; print "{header}" }}\n'
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


def get_fields(path, path_type) -> dict:
    """ Get the fields from the first line of the file_spec or the first csv file in the directory.
     Return a dictionary of field names and their index in the csv file.
     Add an empty string key with value 0 for full record match.
        args:
            path: The file or directory to be searched.
            path_type: 'dir' if path is a directory, 'file' if path is a file.

        returns:
            A dictionary of field names and their index in the csv file.
     """
    if path_type == 'dir':
        file_list = [os.path.join(path, f) for f in os.listdir(path)]
        for file in file_list:
            if file.endswith('.csv'):
                with open(file, 'r', encoding='utf-8') as f:
                    fields = f.readline().strip().split('|')
                    ret = {fields[i].strip(): i +
                           1 for i in range(len(fields))}
    else:
        with open(path, 'r', encoding='utf-8') as f:
            fields = f.readline().strip().split('|')
            ret = {fields[i].strip(): i + 1 for i in range(len(fields))}
    # Add {"": 0} to the fields dictionary for full record match
    ret[""] = 0
    return ret


def main():
    """Main function for the greppy utility."""
    # Parse command line arguments.  Expecting a single argument, the greppy match rules file, defaulting to greppy.txt
    parser = argparse.ArgumentParser(
        description='Greppy: A simple grep-like utility')
    parser.add_argument('config_file', nargs='?',
                        default='greppy.txt', help='Greppy configuration file')
    args = parser.parse_args()

    # Get the file spec from the config file and determine if it is a file or a directory
    path_type, file_spec = get_file_spec(args.config_file)

    # Get the fields from the first line of the file_spec or the first csv file in the directory
    fields = get_fields(file_spec, path_type)

    # Parse the rules from the config file
    match = parse_rules(args.config_file, fields)

    # Generate the awk script
    # Generate a name for the script by replacing '/', '.' or ' ' with '_' in file_spec
    script_name = file_spec.replace(
        '/', '_').replace('.', '_').replace(' ', '_') + '.awk'

    awk_script = generate_awk_script(match, fields)

    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(awk_script)

    # Generate a list of files to process.  If the file_spec is a file, just process that file.
    # If it is a directory, add all files in the directory to the list.
    if path_type == 'dir':
        file_list = [os.path.join(file_spec, f) for f in os.listdir(file_spec)]
    else:
        file_list = [file_spec]

    # Execute the awk script on each file, printing the file name, then the results.
    for file in file_list:
        print(f"Results for {file}")
        proc = subprocess.run(['gawk', '-f', script_name, file],
                              check=True, stdout=subprocess.PIPE)
        proc_stdout = proc.stdout.decode('utf-8')
        print(proc_stdout)


if __name__ == '__main__':
    main()
