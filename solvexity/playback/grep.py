#!/usr/bin/env python3
"""
Custom grep implementation in Python.
Supports searching for simple string patterns in files or from stdin (pipe).
"""

import argparse
import sys
from typing import List, TextIO
import re


def grep_file(file_handle: TextIO, pattern: str, 
              case_insensitive: bool = False,
              line_numbers: bool = False,
              invert_match: bool = False,
              count_only: bool = False,
              use_regex: bool = False,
              filename: str = None) -> int:
    """
    Search for pattern in a file handle.
    
    Args:
        file_handle: File handle to search
        pattern: Pattern to search for
        case_insensitive: If True, perform case-insensitive search
        line_numbers: If True, print line numbers
        invert_match: If True, print lines that don't match
        count_only: If True, only print count of matching lines
        use_regex: If True, treat pattern as regex
        filename: Name of the file (for display purposes)
    
    Returns:
        Number of matching lines
    """
    match_count = 0
    
    # Prepare pattern
    if use_regex:
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            print(f"Invalid regex pattern: {e}", file=sys.stderr)
            sys.exit(2)
        match_func = lambda line: compiled_pattern.search(line)
    else:
        # Simple string search
        search_pattern = pattern.lower() if case_insensitive else pattern
        if case_insensitive:
            match_func = lambda line: search_pattern in line.lower()
        else:
            match_func = lambda line: pattern in line
    
    # Process file line by line
    for line_num, line in enumerate(file_handle, start=1):
        # Remove trailing newline for processing
        line_content = line.rstrip('\n')
        
        # Check if line matches
        matches = match_func(line_content)
        
        # Invert match if needed
        if invert_match:
            matches = not matches
        
        if matches:
            match_count += 1
            if not count_only:
                # Build output line
                output_parts = []
                
                # Add filename if multiple files
                if filename:
                    output_parts.append(f"{filename}:")
                
                # Add line number if requested
                if line_numbers:
                    output_parts.append(f"{line_num}:")
                
                # Add the actual line
                output_parts.append(line_content)
                
                print(''.join(output_parts))
    
    # Print count if requested
    if count_only:
        if filename:
            print(f"{filename}:{match_count}")
        else:
            print(match_count)
    
    return match_count


def main():
    """Main entry point for grep utility."""
    parser = argparse.ArgumentParser(
        description='Search for patterns in files or stdin',
        epilog='Examples:\n'
               '  grep.py "error" file.log\n'
               '  cat file.log | grep.py "error"\n'
               '  grep.py -i "ERROR" file1.log file2.log\n'
               '  grep.py -n -r "^[0-9]+" data.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'pattern',
        type=str,
        help='Pattern to search for'
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        type=str,
        help='Files to search (if not provided, reads from stdin)'
    )
    
    parser.add_argument(
        '-i', '--ignore-case',
        action='store_true',
        help='Perform case-insensitive search'
    )
    
    parser.add_argument(
        '-n', '--line-number',
        action='store_true',
        help='Print line numbers with output lines'
    )
    
    parser.add_argument(
        '-v', '--invert-match',
        action='store_true',
        help='Select non-matching lines'
    )
    
    parser.add_argument(
        '-c', '--count',
        action='store_true',
        help='Only print count of matching lines'
    )
    
    parser.add_argument(
        '-r', '--regex',
        action='store_true',
        help='Treat pattern as regular expression'
    )
    
    parser.add_argument(
        '-H', '--with-filename',
        action='store_true',
        help='Print filename with output lines'
    )
    
    args = parser.parse_args()
    
    total_matches = 0
    exit_code = 1  # Default: no matches found
    
    try:
        # Check if reading from stdin (pipe)
        if not args.files or args.files == ['-']:
            # Read from stdin
            if sys.stdin.isatty():
                # No pipe detected and no files provided
                parser.print_help()
                sys.exit(2)
            
            matches = grep_file(
                sys.stdin,
                args.pattern,
                case_insensitive=args.ignore_case,
                line_numbers=args.line_number,
                invert_match=args.invert_match,
                count_only=args.count,
                use_regex=args.regex,
                filename=None
            )
            total_matches += matches
        else:
            # Read from files
            multiple_files = len(args.files) > 1
            
            for filepath in args.files:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        # Show filename if multiple files or explicitly requested
                        show_filename = (multiple_files or args.with_filename)
                        
                        matches = grep_file(
                            f,
                            args.pattern,
                            case_insensitive=args.ignore_case,
                            line_numbers=args.line_number,
                            invert_match=args.invert_match,
                            count_only=args.count,
                            use_regex=args.regex,
                            filename=filepath if show_filename else None
                        )
                        total_matches += matches
                        
                except FileNotFoundError:
                    print(f"grep.py: {filepath}: No such file or directory", 
                          file=sys.stderr)
                except PermissionError:
                    print(f"grep.py: {filepath}: Permission denied", 
                          file=sys.stderr)
                except Exception as e:
                    print(f"grep.py: {filepath}: {e}", file=sys.stderr)
        
        # Set exit code based on whether matches were found
        if total_matches > 0:
            exit_code = 0  # Matches found
        
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except BrokenPipeError:
        # Handle broken pipe gracefully (e.g., when piping to head)
        sys.exit(0)
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

