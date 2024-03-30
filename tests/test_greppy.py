"""Tests for greppy.py"""
import sys
from runner.greppy import get_file_spec, get_fields, parse_rules, generate_awk_script, main


def test_get_file_spec():
    """Test get_file_spec function"""
    assert get_file_spec(
        './test_column_search.txt') == ('file', 'test_files/test.csv')
    assert get_file_spec('./test_multi_file.txt') == ('dir',
                                                      "./test_files")
    assert get_file_spec('./test_pwd.txt') == ('dir', './test_files')


def test_get_fields():
    """Test get_fields function"""
    expected = {'ProductId': 1, 'ProductPrice': 2,
                'ProductDescription': 3, 'ProductCategory': 4, '': 0}
    assert get_fields('./test_files/test.csv', 'file') == expected
    assert get_fields('./test_files', 'dir') == expected


def test_rules_simple_grep():
    """Test parse_rules function on simple grep"""
    fields = get_fields('./test_files/test.csv', 'file')
    assert parse_rules('./test_pwd.txt', fields) == "$0 ~ /crumpet/"


def test_generate_awk_script_simple_grep():
    """Test generate_awk_script function on simple grep"""
    fields = get_fields('./test_files/test.csv', 'file')
    match = parse_rules('./test_pwd.txt', fields)
    script_lines = generate_awk_script(match, fields).split('\n')
    assert script_lines[
        0] == 'BEGIN { FS="|"; print "ProductId|ProductPrice|ProductDescription|ProductCategory|" }'
    assert script_lines[1] == 'NR > 1 && $0 ~ /crumpet/  { print $0 }'


def test_main_simple_grep(capsys):
    """Test main function on simple grep"""
    sys.argv = ['./greppy.py', './test_pwd.txt']
    main()
    captured = capsys.readouterr().out.split('\n')
    assert captured[0] == 'Results for ./test_files/test.csv'
    assert captured[1] == 'ProductId|ProductPrice|ProductDescription|ProductCategory|'
    assert captured[2] == '1121 | 7.50 | fancy crumpets | grocery'
    assert captured[3] == '1122 | 3.00 | plain crumpets | grocery'
    assert captured[4] == '1125 | 1.00 | sugar crumpets | "snacks"'


def test_rules_column_search():
    """Test parse_rules function on simple grep"""
    fields = get_fields('./test_files/test.csv', 'file')
    assert parse_rules('./test_column_search.txt',
                       fields) == '$1 ~ /^[ ]*"?1128"?[ ]*$/'


def test_generate_awk_script_column_search():
    """Test generate_awk_script function on simple grep"""
    fields = get_fields('./test_files/test.csv', 'file')
    match = parse_rules('./test_column_search.txt', fields)
    script_lines = generate_awk_script(match, fields).split('\n')
    assert script_lines[
        0] == 'BEGIN { FS="|"; print "ProductId|ProductPrice|ProductDescription|ProductCategory|" }'
    assert script_lines[1] == 'NR > 1 && $1 ~ /^[ ]*"?1128"?[ ]*$/  { print $0 }'


def test_main_column_search(capsys):
    """Test main function on simple grep"""
    sys.argv = ['./greppy.py', './test_column_search.txt']
    main()
    captured = capsys.readouterr().out.split('\n')
    assert captured[0] == 'Results for test_files/test.csv'
    assert captured[1] == 'ProductId|ProductPrice|ProductDescription|ProductCategory|'
    assert captured[2] == '1128 || "peanut butter dog treats" | pets'


def test_parse_rules_not_or():
    """Test parse_rules function on negated disjunction"""
    fields = get_fields('./test_files/test.csv', 'file')
    assert parse_rules('./test_multi_file.txt',
                       fields) == "!($1 ~ /^(1123|1128|1129) $/ || $3 ~ /crumpets/)"


def test_generate_awk_script_not_or():
    """Test generate_awk_script function on negated disjunction"""
    fields = get_fields('./test_files/test.csv', 'file')
    match = parse_rules('./test_multi_file.txt', fields)
    script_lines = generate_awk_script(match, fields).split('\n')
    assert script_lines[
        0] == 'BEGIN { FS="|"; print "ProductId|ProductPrice|ProductDescription|ProductCategory|" }'
    assert script_lines[
        1] == 'NR > 1 && !($1 ~ /^(1123|1128|1129) $/ || $3 ~ /crumpets/)  { print $0 }'


def test_main_not_or(capsys):
    """Test main function pr negated disjunction"""
    sys.argv = ['./greppy.py', './test_multi_file.txt']
    main()
    captured = capsys.readouterr().out.split('\n')
    assert captured[0] == 'Results for ./test_files/test.csv'
    assert captured[1] == 'ProductId|ProductPrice|ProductDescription|ProductCategory|'
    assert captured[2] == '1124| 2.00 | Salty jerky treads | pets'
    assert captured[3] == '1126 | 1.00 | plain peanut butter | grocery'
    assert captured[4] == '1127 | 2.00 | peanut brittle | snacks'
    assert captured[5] == '| | 1.00 | mystery cheeze | grocery'
    assert captured[6] == '11293 | 1.00 | mystery cheeze | grocery'


def test_parse_rules_not_and():
    """Test parse_rules function on negated disjunction"""
    fields = get_fields('./test_files/test.csv', 'file')
    assert parse_rules('./test_and.txt',
                       fields) == '$3 ~ /nut/ && $4 !~ /^[ ]*"?snacks"?[ ]*$/'


def test_generate_awk_script_not_and():
    """Test generate_awk_script function on negated disjunction"""
    fields = get_fields('./test_files/test.csv', 'file')
    match = parse_rules('./test_and.txt', fields)
    script_lines = generate_awk_script(match, fields).split('\n')
    assert script_lines[
        0] == 'BEGIN { FS="|"; print "ProductId|ProductPrice|ProductDescription|ProductCategory|" }'
    assert script_lines[
        1] == 'NR > 1 && $3 ~ /nut/ && $4 !~ /^[ ]*"?snacks"?[ ]*$/  { print $0 }'


def test_main_not_and(capsys):
    """Test main function for AND search with negation."""
    sys.argv = ['./greppy.py', './test_and.txt']
    # Product description contains 'nut' and product category is not 'snacks'
    main()
    captured = capsys.readouterr().out.split('\n')
    print(captured)
    assert captured[0] == 'Results for test_files/test.csv'
    assert captured[1] == 'ProductId|ProductPrice|ProductDescription|ProductCategory|'
    assert captured[2] == '1126 | 1.00 | plain peanut butter | grocery'
    assert captured[3] == '1128 || "peanut butter dog treats" | pets'
    assert captured[4] == '1129 | 3.00 | peanuts ||'