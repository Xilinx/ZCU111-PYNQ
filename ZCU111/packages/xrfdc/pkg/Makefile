EMBEDDEDSW_DIR ?= embeddedsw

ESW_LIBS := rfdc scugic
LIB_NAME := libxrfdc.so

ESW_SRC := $(filter-out %_g.c, $(foreach lib, $(ESW_LIBS), $(wildcard $(EMBEDDEDSW_DIR)/XilinxProcessorIPLib/drivers/$(lib)/src/*.c)))
ESW_INC := $(patsubst %, -I$(EMBEDDEDSW_DIR)/XilinxProcessorIPLib/drivers/%/src, $(ESW_LIBS))
OS_INC := -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/common -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/arm/cortexa53/64bit -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/arm/common/gcc -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/arm/common
LOCAL_SRC := $(wildcard src/*.c)
OTHER_INC := -Ilibmetal_include

all: $(LIB_NAME)

$(LIB_NAME): $(EMBEDDEDSW_DIR)
	gcc -o $(LIB_NAME) -shared -fPIC $(ESW_INC) -Isrc $(ESW_SRC) $(LOCAL_SRC) $(OS_INC) $(OTHER_INC) -D__BAREMETAL__ -ggdb

install:
	cp $(LIB_NAME) xrfdc/$(LIB_NAME)
	pip3 install .

$(EMBEDDEDSW_DIR):
	git clone https://github.com/Xilinx/embeddedsw -b release-2018.2 $(EMBEDDEDSW_DIR)
