"""
Run the FortranDep project from the command line

Usage:
    fortrandep [options]

Options:
    --help   Print this message
"""

if __name__ == "__main__":

    from docopt import docopt
    from fortrandep import FortranPackage

    args = docopt(__doc__)

    # build the project

    # output the results

