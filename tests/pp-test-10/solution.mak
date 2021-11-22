#: pp-test-10/data_types.f90
odir/data_types.o : pp-test-10/data_types.f90
#: pp-test-10/src2/vars.f90
odir/vars.o : odir/data_types.o
odir/vars.o : pp-test-10/src2/vars.f90
#: pp-test-10/src1/main.f90
odir/main.o : odir/data_types.o
odir/main.o : odir/vars.o
odir/main.o : pp-test-10/src1/main.f90
#: xmain
xmain : odir/main.o
xmain : odir/vars.o
xmain : odir/data_types.o

