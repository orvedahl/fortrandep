#: test-6/data_types.f90
test-6/data_types.o : test-6/data_types.f90
#: test-6/src2/vars.f90
test-6/src2/vars.o : test-6/data_types.o
test-6/src2/vars.o : test-6/src2/vars.f90
#: test-6/src1/main.f90
test-6/src1/main.o : test-6/data_types.o
test-6/src1/main.o : test-6/src2/vars.o
test-6/src1/main.o : test-6/src1/main.f90
#: xmain
xmain : test-6/src2/vars.o
xmain : test-6/data_types.o
xmain : test-6/src1/main.o

