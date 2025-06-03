
VITIS_HLS_BIN := $(shell which vitis_hls)
ifeq ($(VITIS_HLS_BIN),)
  $(error "Error: vitis_hls not found in PATH")
endif


VITIS_HLS_DIST_PATH  := $(shell dirname $(shell dirname $(VITIS_HLS_BIN)))
LIB_PATH_1           := $(VITIS_HLS_DIST_PATH)/lib/lnx64.o
LIB_PATH_2           := $(VITIS_HLS_DIST_PATH)/lnx64/lib/csim


CLANG_FORMAT_PATH := $(VITIS_HLS_DIST_PATH)/lnx64/tools/clang-3.9-csynth/bin/clang-format
ifeq ("$(wildcard $(CLANG_FORMAT_PATH))","")
  $(error "Error: Could not find clang-format at $(CLANG_FORMAT_PATH)")
endif


LD_LIB_EXPORT := LD_LIBRARY_PATH=$(LIB_PATH_1):$(LIB_PATH_2):$$LD_LIBRARY_PATH


SRCS := $(shell find ./hls_eval_data -type f -name '*.cpp')
HEADERS := $(shell find ./hls_eval_data -type f -name '*.h')
FORMATTED_FILES := $(SRCS) $(HEADERS)

# $(info FORMATTED_FILES is: $(FORMATTED_FILES))

# print out clang format version
$(info "Using clang-format at $(CLANG_FORMAT_PATH)")
$(info "clang-format version: $(shell $(LD_LIB_EXPORT) $(CLANG_FORMAT_PATH) --version)")



.PHONY: format
format:
	@for file in $(FORMATTED_FILES); do \
		echo "Formatting $$file"; \
		$(LD_LIB_EXPORT) $(CLANG_FORMAT_PATH) -i $$file; \
	done
	@echo "All files formatted."


