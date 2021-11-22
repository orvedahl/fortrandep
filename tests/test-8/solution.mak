#: test-8/data_types.f90
build/data_types.o : test-8/data_types.f90
#: test-8/src2/vars.f90
build/vars.o : build/data_types.o
build/vars.o : test-8/src2/vars.f90
#: test-8/src1/main.f90
build/main.o : build/data_types.o
build/main.o : build/vars.o
build/main.o : test-8/src1/main.f90
#: xmain
xmain : build/main.o
xmain : build/vars.o
xmain : build/data_types.o

