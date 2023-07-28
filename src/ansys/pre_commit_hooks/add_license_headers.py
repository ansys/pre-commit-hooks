#!/usr/bin/env python
# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Run reuse for files missing license headers."""
import argparse
import datetime
import os
import sys
import json
import git
from tempfile import NamedTemporaryFile
from reuse import lint, header, project

def find_files_missing_header():
    """
    Retrieve files without license header.
    
    Returns:
        0: No files exist that are missing license header.
        1: Files exist that are missing license header.
    """
    # Set up argparse for location, parser, and lint
    # Lint contains 4 args: quiet, json, plain, and no_multiprocessing
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loc", type=str, required=True, help="Path to repository location", default="src"
    )
    parser.add_argument(
        "--parser", 
    )
    parser.add_argument("--no_multiprocessing", action="store_true")
    lint.add_arguments(parser)
    
    args = parser.parse_args([sys.argv[1]])
    proj = project.Project(fr'{args.loc}') 
    
    # Create a temporary file containing lint.run json output
    with NamedTemporaryFile(mode="w", delete=False) as tmp:
        args.json = True
        lint.run(args, proj, tmp)
    # Open the temporary file, load the json, and find files missing copyright and/or licensing info.
    file = open(tmp.name , "rb" )
    lint_json = json.load(file)
    file.close()
    missing_headers = list(set(lint_json['non_compliant']['missing_copyright_info'] + lint_json['non_compliant']['missing_licensing_info']))
    
    # Remove temporary file
    os.remove(tmp.name)
    
    # Get current year for license file
    year = datetime.date.today().year
    
    # If there are files missing headers, run reuse and return 1
    if missing_headers != []:
        run_reuse(parser, year, args.loc, missing_headers)
        return 1
    return 0
            
 
def run_reuse(parser, year, loc, missing_headers):
    """
    Run reuse command on files without license headers.
    Args:
        parser (argparse.ArgumentParser): Parser containing previously set arguments. 
        year (int): Current year for license header.
        loc (str): Location to search for files missing headers.
        missing_headers (list): List of files that are missing headers.
    Returns:
        1: Fails pre-commit hook on return 1
    """
    
    # Add header arguments to parser which include: copyright, license, contributor, year, 
    # style, copyright-style, template, exclude-year, merge-copyrights, single-line, 
    # multi-line, explicit-license, force-dot-license, recursive, no-replace, 
    # skip-unrecognized, skip-existing
    header.add_arguments(parser)   
    
    # Get root directory of current git repository
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    
    # If .reuse folder does not exist in git repository root, throw error
    if not os.path.isdir(os.path.join(git_root,".reuse")): 
        print(f"Please ensure the .reuse directory is in {git_root}")  
        return 1
       
    # Add missing license header to each file in the list
    for file in missing_headers:
        args = parser.parse_args([fr'--loc={loc}', file])
        args.year = [ str(year) ]
        args.copyright_style = 'string-c'
        args.copyright = ['ANSYS, Inc. and/or its affiliates.']
        args.merge_copyrights = True  
        args.template = 'ansys'
        args.license = ['MIT']
        args.skip_unrecognised = True
        args.parser = parser
        
        # Requires .reuse directory to be in git_root directory
        proj = project.Project(git_root)
        header.run(args, proj)
    
    return 1

def main():
    """Find files missing license header & run reuse on them."""
    status = find_files_missing_header()
    if status == 1:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover