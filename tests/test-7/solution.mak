#
# This file is generated automatically. DO NOT EDIT!
#
#
#: build_dir = _build/debug/odir
#
#
#: test-7/data_types.f90
_build/debug/odir/data_types.o : test-7/data_types.f90
#: test-7/src2/vars.f90
_build/debug/odir/vars.o : _build/debug/odir/data_types.o
_build/debug/odir/vars.o : test-7/src2/vars.f90
#: test-7/src1/main.f90
_build/debug/odir/main.o : _build/debug/odir/data_types.o
_build/debug/odir/main.o : _build/debug/odir/vars.o
_build/debug/odir/main.o : test-7/src1/main.f90
#: xmain
xmain : _build/debug/odir/data_types.o
xmain : _build/debug/odir/main.o
xmain : _build/debug/odir/vars.o

