import os
import datetime
import subprocess

from reuse import lint
from reuse.project import Project
from reuse.report import ProjectReport
import os.path


def get_files():
    project = Project('./')
    report = ProjectReport.generate(project)
    return lint.lint_files_without_copyright_and_licensing(report)
    
    
def run_reuse(file):
    year = datetime.date.today().year
    cmd = ['reuse', 'annotate', '--year', fr'{year}', '--copyright-style', 'string-c', '--merge-copyright', '--template=ansys', '-l', 'MIT', '-c', 'ANSYS, Inc. and/or its affiliates.', '--skip-unrecognised', fr'{file}']
    subprocess.check_call(cmd)


def main():
    script_loc = os.path.dirname(__file__)
    root_dir = fr'{script_loc}/../../../../'
    os.chdir(root_dir)
    
    # Reuse lint  
    missing_header = get_files()
    
    for file in missing_header:
        if os.path.isfile(file):
            run_reuse(file)

    
if __name__ == '__main__':
    main()