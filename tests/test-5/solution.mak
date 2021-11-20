#
# This file is generated automatically. DO NOT EDIT!
#
#
#: build_dir = 
#
#
#: test-5/data_types.f90
test-5/data_types.o : test-5/data_types.f90
#: test-5/src2/vars.f90
test-5/src2/vars.o : test-5/data_types.o
test-5/src2/vars.o : test-5/src2/vars.f90
#: test-5/src1/main.f90
test-5/src1/main.o : test-5/data_types.o
test-5/src1/main.o : test-5/src2/vars.o
test-5/src1/main.o : test-5/src1/main.f90
#: xmain
xmain : test-5/src2/vars.o
xmain : test-5/data_types.o
xmain : test-5/src1/main.o

