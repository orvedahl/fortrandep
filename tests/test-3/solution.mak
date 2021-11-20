#
# This file is generated automatically. DO NOT EDIT!
#
#
#: build_dir = 
#
#
#: test-3/variables.f90
test-3/variables.o : test-3/variables.f90
#: test-3/main.f90
test-3/main.o : test-3/variables.o
test-3/main.o : test-3/main.f90
#: xmain
xmain : test-3/variables.o
xmain : test-3/main.o

