#
# This file is generated automatically. DO NOT EDIT!
#
#
#: build_dir = odir
#
#
#: pp-test-16/data_types.f90
odir/data_types.o : pp-test-16/data_types.f90
#: pp-test-16/src2/vars.f90
odir/vars.o : odir/data_types.o
odir/vars.o : pp-test-16/src2/vars.f90
#: pp-test-16/src2/moduleC.f90
odir/moduleC.o : odir/data_types.o
odir/moduleC.o : pp-test-16/src2/moduleC.f90
#: pp-test-16/src1/main.f90
odir/main.o : odir/moduleC.o
odir/main.o : odir/vars.o
odir/main.o : pp-test-16/src1/main.f90
#: xmain
xmain : odir/vars.o
xmain : odir/main.o
xmain : odir/data_types.o
xmain : odir/moduleC.o

