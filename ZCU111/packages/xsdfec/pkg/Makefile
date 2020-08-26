EMBEDDEDSW_DIR ?= embeddedsw

ESW_LIBS := sd_fec scugic
LIB_NAME := libxsdfec.so

LIB_METAL_DIR := $(EMBEDDEDSW_DIR)/ThirdParty/sw_services/libmetal/src/libmetal
LIB_METAL_INC := $(LIB_METAL_DIR)/build-libmetal/lib/include

ESW_SRC := $(filter-out %_g.c, $(foreach lib, $(ESW_LIBS), $(wildcard $(EMBEDDEDSW_DIR)/XilinxProcessorIPLib/drivers/$(lib)/src/*.c)))
ESW_INC := $(patsubst %, -I$(EMBEDDEDSW_DIR)/XilinxProcessorIPLib/drivers/%/src, $(ESW_LIBS))
OS_INC := -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/common -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/arm/ARMv8/64bit -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/arm/ARMv8/64bit/platform/ZynqMP -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/arm/common/gcc -I$(EMBEDDEDSW_DIR)/lib/bsp/standalone/src/arm/common -I$(LIB_METAL_INC)
LOCAL_SRC := $(wildcard src/*.c)

all: $(LIB_NAME)

$(LIB_NAME): $(EMBEDDEDSW_DIR) $(LIB_METAL_INC)
	gcc -o $(LIB_NAME) -shared -fPIC $(ESW_INC) -Isrc $(ESW_SRC) $(LOCAL_SRC) $(OS_INC) -D__BAREMETAL__ -ggdb

install:
	cp $(LIB_NAME) xsdfec/$(LIB_NAME)
	pip3 install .

$(EMBEDDEDSW_DIR):
	git clone https://github.com/Xilinx/embeddedsw -b release-2020.1 $(EMBEDDEDSW_DIR)

$(LIB_METAL_INC): $(EMBEDDED_DIR)
	apt install -y libsysfs-dev
	mkdir -p $(LIB_METAL_DIR)/build-libmetal;
	cd $(LIB_METAL_DIR)/build-libmetal; \
	cmake .. -DCMAKE_TOOLCHAIN_FILE=/../../../../../../../zcu111-libmetal.cmake

