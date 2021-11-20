#
# This file is generated automatically. DO NOT EDIT!
#
#
#: build_dir = build
#
#
#: test-16/data_types.f90
build/data_types.o : test-16/data_types.f90
#: test-16/src2/vars.f90
build/vars.o : build/data_types.o
build/vars.o : test-16/src2/vars.f90
#: test-16/src1/main.f90
build/main.o : build/data_types.o
build/main.o : build/vars.o
build/main.o : test-16/src1/main.f90
#: xmain
xmain : build/data_types.o
xmain : build/vars.o
xmain : build/main.o

