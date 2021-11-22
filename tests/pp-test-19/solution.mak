#: pp-test-19/data_types.f90
odir/data_types.o : pp-test-19/data_types.f90
#: pp-test-19/src2/moduleC.f90
odir/moduleC.o : odir/vars.o
odir/moduleC.o : pp-test-19/src2/moduleC.f90
#: pp-test-19/src2/vars.f90
odir/vars.o : odir/data_types.o
odir/vars.o : pp-test-19/src2/vars.f90
#: pp-test-19/src1/main.f90
odir/main.o : odir/data_types.o
odir/main.o : odir/moduleC.o
odir/main.o : pp-test-19/src1/main.f90
#: xmain
xmain : odir/moduleC.o
xmain : odir/vars.o
xmain : odir/data_types.o
xmain : odir/main.o

