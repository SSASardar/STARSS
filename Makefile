# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -Iinclude
# Enable AddressSanitizer for memory debugging (commented out for ARM64 compatibility)
# ASAN_FLAGS = -fsanitize=address -g -O1

# Directories
SRC_DIR = src
BUILD_DIR = build
TEST_DIR = tests

# Source files and object files
SRC_FILES := $(wildcard $(SRC_DIR)/*.c)
OBJ_FILES := $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(SRC_FILES))

# Target executable
TARGET = rain

# Default target
all: $(TARGET)

# Linking the final executable
$(TARGET): $(OBJ_FILES)
	$(CC) $(OBJ_FILES) -o $@

# Compile each .c file in src/ to build/*.o
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Run the app
run: all
	./$(TARGET)

# ------------------------------
# Testing support
# All source files except main.c
SRC_NO_MAIN := $(filter-out $(SRC_DIR)/main.c, $(SRC_FILES))

# Build and run all tests
tests: $(wildcard $(TEST_DIR)/*.c)
	@mkdir -p $(BUILD_DIR)
	@for test_src in $^; do \
		test_exe="$(BUILD_DIR)/$$(basename $$test_src .c)"; \
		echo "🔧 Building $$test_src"; \
		$(CC) $(CFLAGS) $$test_src $(SRC_NO_MAIN) -o $$test_exe || exit 1; \
		echo "✅ Running $$test_exe"; \
		./$$test_exe || exit 1; \
	done

# Run individual test by name or list available tests
test:
ifeq ($(strip $(TEST)),)
	@echo "🧪 Available tests:"
	@tests=($(wildcard $(TEST_DIR)/*.c)); \
	for i in $${!tests[@]}; do \
		name=$$(basename $${tests[i]} .c); \
		echo "  $$((i+1)). $$name"; \
	done; \
	printf "\nEnter test number to run (or 0 to cancel): "; \
	read num; \
	if [ "$$num" -eq 0 ]; then \
		echo "Cancelled."; \
		exit 0; \
	elif [ "$$num" -ge 1 ] && [ "$$num" -le $${#tests[@]} ]; then \
		selected_test=$${tests[$$((num-1))]}; \
		test_name=$$(basename $$selected_test .c); \
		echo "🔧 Building $$selected_test"; \
		mkdir -p $(BUILD_DIR); \
		out_file="$(BUILD_DIR)/$$test_name"; \
		$(CC) $(CFLAGS) $$selected_test $(SRC_NO_MAIN) -o $$out_file && \
		echo "✅ Running $$out_file"; \
		./$$out_file; \
	else \
		echo "❌ Invalid selection."; \
		exit 1; \
	fi
else
	@mkdir -p $(BUILD_DIR)
	@src_file="$(TEST_DIR)/$(TEST).c"; \
	out_file="$(BUILD_DIR)/$(TEST)"; \
	if [ ! -f "$$src_file" ]; then \
		echo "❌ Test $$src_file not found"; exit 1; \
	fi; \
	echo "🔧 Building $$src_file"; \
	$(CC) $(CFLAGS) $$src_file $(SRC_NO_MAIN) -o $$out_file && \
	echo "✅ Running $$out_file"; \
	./$$out_file
endif

# ---------------------------------
# Project management progress report
PROGRESS_SRC = project_management/current_progress.c
PROGRESS_EXE = $(BUILD_DIR)/progress_report

progress: $(PROGRESS_EXE)
	@echo "📊 Generating progress report..."
	./$(PROGRESS_EXE)

$(PROGRESS_EXE): $(PROGRESS_SRC)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) $(PROGRESS_SRC) -o $(PROGRESS_EXE)

# Clean everything
clean:
	rm -rf $(BUILD_DIR)/* $(TARGET)

.PHONY: all clean run tests test progress
