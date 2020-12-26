#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020-2021 Pi-Yueh Chuang and Lorena A. Barba
#
# Distributed under terms of the BSD 3-Clause license.

"""Main function of geoclaw-landspill.
"""
import pathlib
import argparse
import subprocess
import gclandspill
from gclandspill._create_data import create_data
from gclandspill._postprocessing import convert_to_netcdf


def main():
    """Main function of geoclaw-landspill."""

    # main CMD parser
    parser = argparse.ArgumentParser(
        description="""
        Hydrocarbon overland spill solver and utilities.\n
        Use `geoclaw-landspill <COMMAND> --help` to see the usage of each command.
        """,
        epilog="GitHub page: https://github.com/barbagroup/geoclaw-landspill"
    )

    parser.add_argument(
        "--version", action='version', version='%(prog)s {}'.format(gclandspill.__version__))

    # subparser group
    subparsers = parser.add_subparsers(dest="cmd", metavar="<COMMAND>", required=True)

    # `run` command
    # ----------------------------------------------------------------------------------------------
    parser_run = subparsers.add_parser(
        name="run", help="Run a simulation.", description="Run a simulation.")

    parser_run.add_argument(
        "case", action="store", type=pathlib.Path, metavar="CASE",
        help="The path to the target case directory."
    )

    parser_run.set_defaults(func=run)  # set the corresponding callback for the `run` command

    # `createnc` command
    # ----------------------------------------------------------------------------------------------
    parser_createnc = subparsers.add_parser(
        name="createnc", help="Convert simulation results to NetCDF file with CF convention.",
        description="Convert simulation results to NetCDF file with CF convention."
    )

    # path to the case directory
    parser_createnc.add_argument(
        "case", action="store", type=pathlib.Path, metavar="CASE",
        help="The path to the target case directory."
    )

    parser_createnc.add_argument(
        '--level', dest="level", action="store", type=int,
        help='Use data from a specific AMR level (default: finest level)')

    parser_createnc.add_argument(
        '--frame-bg', dest="frame_bg", action="store", type=int, default=0, metavar="FRAMEBG",
        help='Customize beginning frame No. (default: 0)')

    parser_createnc.add_argument(
        '--frame-ed', dest="frame_ed", action="store", type=int, metavar="FRAMEED",
        help='Customize end frame No. (default: get from setrun.py)')

    parser_createnc.add_argument(
        '--soln-dir', dest="soln_dir", action="store", type=pathlib.Path, default="_output",
        metavar="SOLNDIR", help="""
            Customize the folder holding solution files. A relative path will be assumed to be
            relative to CASE. (default: _output)
        """)

    parser_createnc.add_argument(
        '--dest-dir', dest="dest_dir", action="store", type=pathlib.Path, metavar="DESTDIR",
        help="""
            Customize the folder to save output file. A relative path will be assumed to be
            relative to CASE. Ignored if FILENAME is an absolute path. (default: same as SOLNDIR)')
        """)

    parser_createnc.add_argument(
        '--filename', dest="filename", action="store", type=pathlib.Path,
        help="""
            Customize the output raster file name. A relative path will be assumed to be
            relative to DESTDIR. (default: case name + level)
        """)

    parser_createnc.add_argument(
        '--extent', dest="extent", action="store", nargs=4, type=float, default=None,
        metavar=("XMIN", "YMIN", "XMAX", "YMAX"),
        help='Customize the output raster extent (default: determine from solutions)')

    parser_createnc.add_argument(
        '--res', dest="res", action="store", type=float, default=None,
        help='Customize the output raster resolution (default: determine from solutions)')

    parser_createnc.add_argument(
        '--dry-tol', dest="dry_tol", action="store", type=float, default=None,
        help='Customize the dry tolerance (default: get from setrun.py)')

    parser_createnc.add_argument(
        '--nodata', dest="nodata", action="store", type=int, default=-9999,
        help='Customize the nodata value (default: -9999)')

    parser_createnc.add_argument(
        "--use-case-settings", dest="use_case_settings", action="store_true",
        help="Use the timestamp settings in case_settings.txt under CASE")

    parser_createnc.set_defaults(func=convert_to_netcdf)  # callback for the `createnc` command

    # parse the cmd
    args = parser.parse_args()

    # execute the corresponding subcommand and return code
    return args.func(args)


def run(args: argparse.Namespace):
    """Run a simulation using geoclaw-landspill Fortran binary.

    This function should be called by `main()`.

    Arguments
    ---------
    args : argparse.Namespace
        The CMD arguments parsed by `argparse` package.

    Returns
    -------
    Execution code. 0 means all good. Other values means something wrong.
    """

    # process path
    args.case = args.case.expanduser().resolve()
    assert args.case.is_dir()

    # the output folder of simulation results of this run
    args.output = args.case.joinpath("_output")

    # create *.data files, topology files, and hydrological file
    create_data(args.case, args.output)

    # get the Fortran solver binary
    solver = pathlib.Path(gclandspill.__file__).parents[1].joinpath("bin", "geoclaw-landspill-bin")

    if not solver.is_file():
        raise FileNotFoundError("Couldn't find solver at {}".format(solver))

    # execute the solver
    result = subprocess.run(solver, capture_output=False, cwd=str(args.output), check=True)

    return result.returncode


if __name__ == "__main__":
    import sys
    sys.exit(main())
