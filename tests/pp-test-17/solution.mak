#: pp-test-17/data_types.f90
odir/data_types.o : pp-test-17/data_types.f90
#: pp-test-17/src2/moduleC.f90
odir/moduleC.o : odir/vars.o
odir/moduleC.o : pp-test-17/src2/moduleC.f90
#: pp-test-17/src1/main.f90
odir/main.o : odir/data_types.o
odir/main.o : pp-test-17/src1/main.f90
#: pp-test-17/src2/vars.f90
odir/vars.o : odir/data_types.o
odir/vars.o : pp-test-17/src2/vars.f90
#: xmain
xmain : odir/main.o
xmain : odir/data_types.o

