#: pp-test-15/data_types.f90
odir/data_types.o : pp-test-15/data_types.f90
#: pp-test-15/src2/vars.f90
odir/vars.o : odir/data_types.o
odir/vars.o : pp-test-15/src2/vars.f90
#: pp-test-15/src1/main.f90
odir/main.o : odir/vars.o
odir/main.o : pp-test-15/src1/main.f90
#: xmain
xmain : odir/vars.o
xmain : odir/main.o

