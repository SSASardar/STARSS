# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -Iinclude -I. -lm -D_GNU_SOURCE
# Enable AddressSanitizer for memory debugging (commented out for ARM64 compatibility)
# ASAN_FLAGS = -fsanitize=address -g -O1

# Directories
SRC_DIR = src
BUILD_DIR = build
TEST_DIR = tests
OUTPUTS_DIR = outputs
BATCH_DIR = batch_test_$(shell date +%Y%m%d_%H%M%S)

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

# ------------------------------
# Simplified direct compilation for batch testing

# Build the test executable without running
build-test:
	@mkdir -p $(BUILD_DIR)
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify TEST name. Usage: make build-test TEST=test_cl"; \
		exit 1; \
	fi
	@src_file="$(TEST_DIR)/$(TEST).c"; \
	out_file="$(BUILD_DIR)/$(TEST)"; \
	if [ ! -f "$$src_file" ]; then \
		echo "❌ Test $$src_file not found"; exit 1; \
	fi; \
	echo "🔧 Building $$src_file"; \
	$(CC) $(CFLAGS) $$src_file $(SRC_NO_MAIN) -o $$out_file; \
	if [ $$? -eq 0 ]; then \
		echo "✅ Build successful: $$out_file"; \
	else \
		echo "❌ Build failed"; \
		exit 1; \
	fi

# Run already built test with arguments
run-test:
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify TEST name. Usage: make run-test TEST=test_cl ARGS='-r 500'"; \
		exit 1; \
	fi
	@out_file="$(BUILD_DIR)/$(TEST)"; \
	if [ ! -f "$$out_file" ]; then \
		echo "❌ Test executable not found. Run 'make build-test TEST=$(TEST)' first."; \
		exit 1; \
	fi; \
	echo "✅ Running $$out_file with args: $(ARGS)"; \
	./$$out_file $(ARGS)

# One-liner: Build and run with arguments (useful for single runs)
quick-test:
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify TEST name. Usage: make quick-test TEST=test_cl ARGS='-r 500'"; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory build-test TEST=$(TEST)
	@$(MAKE) --no-print-directory run-test TEST=$(TEST) ARGS="$(ARGS)"

# Batch test with multiple parameter combinations from a file (Serial)
# Usage: make batch-test TEST=test_cl PARAM_FILE=params.txt
batch-test:
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify TEST name"; \
		exit 1; \
	fi
	@if [ -z "$(PARAM_FILE)" ]; then \
		echo "❌ Please specify PARAM_FILE"; \
		exit 1; \
	fi
	@if [ ! -f "$(PARAM_FILE)" ]; then \
		echo "❌ Parameter file $(PARAM_FILE) not found"; \
		exit 1; \
	fi
	@echo "Creating batch directory: $(BATCH_DIR)"
	@mkdir -p "$(BATCH_DIR)"
	@$(MAKE) --no-print-directory build-test TEST=$(TEST)
	@echo "🚀 Running batch tests from $(PARAM_FILE)"
	@echo "========================================"
	@counter=1; \
	total=$$(grep -v '^#' $(PARAM_FILE) | grep -v '^$$' | wc -l | tr -d ' '); \
	echo "Total tests to run: $$total"; \
	echo ""; \
	start_time=$$(date +%s); \
	while IFS= read -r params; do \
		if [ ! -z "$$params" ] && [ "$$params" != "$$(echo $$params | cut -c1)#" ]; then \
			test_start=$$(date +%s); \
			echo "📊 Test $$counter/$$total: $$params"; \
			\
			r_val=$$(echo "$$params" | sed -n 's/.*-r \([0-9]*\).*/\1/p'); \
			m_val=$$(echo "$$params" | sed -n 's/.*-m \([0-9]*\).*/\1/p'); \
			c_val=$$(echo "$$params" | sed -n 's/.*-c \([0-9]*\).*/\1/p'); \
			k_val=$$(echo "$$params" | sed -n 's/.*-k \([0-9.]*\).*/\1/p'); \
			y_val=$$(echo "$$params" | sed -n 's/.*-y \([0-9]*\).*/\1/p'); \
			a_val=$$(echo "$$params" | sed -n 's/.*-a \([0-9.]*\).*/\1/p'); \
			\
			if [ -z "$$r_val" ]; then r_val="0000"; else r_val=$$(printf "%04d" $$r_val); fi; \
			if [ -z "$$m_val" ]; then m_val="000"; else m_val=$$(printf "%03d" $$m_val); fi; \
			if [ -z "$$c_val" ]; then c_val="0000"; else c_val=$$(printf "%04d" $$c_val); fi; \
			if [ -z "$$k_val" ]; then k_val="000"; else k_val=$$(printf "%03d" $$(echo "$$k_val * 100" | bc | cut -d. -f1)); fi; \
			if [ -z "$$y_val" ]; then y_val="000000"; else y_val=$$(printf "%06d" $$y_val); fi; \
			if [ -z "$$a_val" ]; then a_val="00"; else a_val=$$(printf "%02d" $$(echo "$$a_val + 0.5" | bc | cut -d. -f1)); fi; \
			\
			stats_filename="stats_r_$${r_val}_m_$${m_val}_c_$${c_val}_k_$${k_val}_y_$${y_val}_a_$${a_val}.txt"; \
			echo "   Output file: $(BATCH_DIR)/$$stats_filename"; \
			\
			rm -f $(OUTPUTS_DIR)/*.txt; \
			\
			./$(BUILD_DIR)/$(TEST) $$params; \
			\
			if [ -f "$(OUTPUTS_DIR)/stats.txt" ]; then \
				mv "$(OUTPUTS_DIR)/stats.txt" "$(BATCH_DIR)/$$stats_filename"; \
				echo "   ✅ Saved to $(BATCH_DIR)/$$stats_filename"; \
			else \
				echo "   ⚠️ Warning: stats.txt not found"; \
			fi; \
			\
			test_end=$$(date +%s); \
			test_duration=$$((test_end - test_start)); \
			echo "   ⏱️  Duration: $$test_duration seconds"; \
			\
			current_time=$$(date +%s); \
			elapsed=$$((current_time - start_time)); \
			avg_time=$$((elapsed / counter)); \
			remaining=$$((avg_time * (total - counter))); \
			remaining_min=$$((remaining / 60)); \
			remaining_sec=$$((remaining % 60)); \
			echo "   📈 Progress: $$counter/$$total completed"; \
			echo "   ⏰ Elapsed: $$((elapsed / 60))m $$((elapsed % 60))s"; \
			echo "   ⏱️  Avg time/test: $$avg_time seconds"; \
			echo "   ⏳ ETA: $$remaining_min minutes $$remaining_sec seconds"; \
			echo ""; \
			counter=$$((counter + 1)); \
		fi; \
	done < $(PARAM_FILE); \
	end_time=$$(date +%s); \
	total_duration=$$((end_time - start_time)); \
	total_min=$$((total_duration / 60)); \
	total_sec=$$((total_duration % 60)); \
	echo "========================================"; \
	echo "✅ Completed $$((counter-1)) test runs"; \
	echo "⏱️  Total time: $$total_min minutes $$total_sec seconds"; \
	echo "📁 Results saved in: $(BATCH_DIR)"

# Parallel batch test with multiple cores (GNU Parallel)
# Usage: make parallel-batch-test TEST=test_cl PARAM_FILE=params.txt CORES=8
parallel-batch-test:
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify TEST name"; \
		exit 1; \
	fi
	@if [ -z "$(PARAM_FILE)" ]; then \
		echo "❌ Please specify PARAM_FILE"; \
		exit 1; \
	fi
	@if [ ! -f "$(PARAM_FILE)" ]; then \
		echo "❌ Parameter file $(PARAM_FILE) not found"; \
		exit 1; \
	fi
	@if [ -z "$(CORES)" ]; then \
		CORES=8; \
		echo "⚠️  CORES not specified, using 8 cores"; \
	fi
	@echo "Creating batch directory: $(BATCH_DIR)"
	@mkdir -p "$(BATCH_DIR)"
	@$(MAKE) --no-print-directory build-test TEST=$(TEST)
	@echo "🚀 Running parallel batch tests from $(PARAM_FILE) on $(CORES) cores"
	@echo "========================================"
	@total=$$(grep -v '^#' $(PARAM_FILE) | grep -v '^$$' | wc -l | tr -d ' '); \
	echo "Total tests to run: $$total"; \
	echo ""; \
	start_time=$$(date +%s); \
	cat $(PARAM_FILE) | grep -v '^#' | grep -v '^$$' | \
	parallel -j $(CORES) --bar \
		'params="{}"; \
		WORKER_ID=$$(printf "%03d" {#}); \
		r_val=$$(echo $$params | sed -n "s/.*-r \([0-9]*\).*/\1/p"); \
		m_val=$$(echo $$params | sed -n "s/.*-m \([0-9]*\).*/\1/p"); \
		c_val=$$(echo $$params | sed -n "s/.*-c \([0-9]*\).*/\1/p"); \
		k_val=$$(echo $$params | sed -n "s/.*-k \([0-9.]*\).*/\1/p"); \
		y_val=$$(echo $$params | sed -n "s/.*-y \([0-9]*\).*/\1/p"); \
		a_val=$$(echo $$params | sed -n "s/.*-a \([0-9.]*\).*/\1/p"); \
		[ -z "$$r_val" ] && r_val="0000" || r_val=$$(printf "%04d" $$r_val); \
		[ -z "$$m_val" ] && m_val="000" || m_val=$$(printf "%03d" $$m_val); \
		[ -z "$$c_val" ] && c_val="0000" || c_val=$$(printf "%04d" $$c_val); \
		[ -z "$$k_val" ] && k_val="000" || k_val=$$(printf "%03d" $$(echo "$$k_val * 100" | bc | cut -d. -f1)); \
		[ -z "$$y_val" ] && y_val="000000" || y_val=$$(printf "%06d" $$y_val); \
		[ -z "$$a_val" ] && a_val="00" || a_val=$$(printf "%02d" $$(echo "$$a_val + 0.5" | bc | cut -d. -f1)); \
		stats_filename="stats_r_$${r_val}_m_$${m_val}_c_$${c_val}_k_$${k_val}_y_$${y_val}_a_$${a_val}.txt"; \
		./$(BUILD_DIR)/$(TEST) $$params -w $$WORKER_ID > /dev/null 2>&1; \
		if [ -f "outputs_$${WORKER_ID}/stats.txt" ]; then \
			mv "outputs_$${WORKER_ID}/stats.txt" "$(BATCH_DIR)/$$stats_filename"; \
		fi; \
		rm -rf outputs_$${WORKER_ID} inputs_$${WORKER_ID} archive_$${WORKER_ID} logs_$${WORKER_ID} 2>/dev/null; \
		' \
	; \
	end_time=$$(date +%s); \
	total_duration=$$((end_time - start_time)); \
	total_min=$$((total_duration / 60)); \
	total_sec=$$((total_duration % 60)); \
	echo ""; \
	echo "========================================"; \
	echo "✅ Parallel batch testing completed"; \
	echo "⏱️  Total time: $$total_min minutes $$total_sec seconds"; \
	echo "📁 Results saved in: $(BATCH_DIR)"


# Adaptive parallel batch test with multiple cores (GNU Parallel)
# Also moves ad_stats.txt files from outputs folder to batch directory
# Usage: make adaptive-parallel-batch-test TEST=test_cl PARAM_FILE=params.txt CORES=8
adaptive-parallel-batch-test:
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify TEST name"; \
		exit 1; \
	fi
	@if [ -z "$(PARAM_FILE)" ]; then \
		echo "❌ Please specify PARAM_FILE"; \
		exit 1; \
	fi
	@if [ ! -f "$(PARAM_FILE)" ]; then \
		echo "❌ Parameter file $(PARAM_FILE) not found"; \
		exit 1; \
	fi
	@if [ -z "$(CORES)" ]; then \
		CORES=8; \
		echo "⚠️  CORES not specified, using 8 cores"; \
	fi
	@echo "Creating batch directory: $(BATCH_DIR)"
	@mkdir -p "$(BATCH_DIR)"
	@$(MAKE) --no-print-directory build-test TEST=$(TEST)
	@echo "🚀 Running adaptive parallel batch tests from $(PARAM_FILE) on $(CORES) cores"
	@echo "📊 This version also collects ad_stats.txt files"
	@echo "========================================"
	@total=$$(grep -v '^#' $(PARAM_FILE) | grep -v '^$$' | wc -l | tr -d ' '); \
	echo "Total tests to run: $$total"; \
	echo ""; \
	start_time=$$(date +%s); \
	cat $(PARAM_FILE) | grep -v '^#' | grep -v '^$$' | \
	parallel -j $(CORES) --bar \
		'params="{}"; \
		WORKER_ID=$$(printf "%03d" {#}); \
		r_val=$$(echo $$params | sed -n "s/.*-r \([0-9]*\).*/\1/p"); \
		m_val=$$(echo $$params | sed -n "s/.*-m \([0-9]*\).*/\1/p"); \
		c_val=$$(echo $$params | sed -n "s/.*-c \([0-9]*\).*/\1/p"); \
		k_val=$$(echo $$params | sed -n "s/.*-k \([0-9.]*\).*/\1/p"); \
		y_val=$$(echo $$params | sed -n "s/.*-y \([0-9]*\).*/\1/p"); \
		a_val=$$(echo $$params | sed -n "s/.*-a \([0-9.]*\).*/\1/p"); \
		[ -z "$$r_val" ] && r_val="0000" || r_val=$$(printf "%04d" $$r_val); \
		[ -z "$$m_val" ] && m_val="000" || m_val=$$(printf "%03d" $$m_val); \
		[ -z "$$c_val" ] && c_val="0000" || c_val=$$(printf "%04d" $$c_val); \
		[ -z "$$k_val" ] && k_val="000" || k_val=$$(printf "%03d" $$(echo "$$k_val * 100" | bc | cut -d. -f1)); \
		[ -z "$$y_val" ] && y_val="000000" || y_val=$$(printf "%06d" $$y_val); \
		[ -z "$$a_val" ] && a_val="00" || a_val=$$(printf "%02d" $$(echo "$$a_val + 0.5" | bc | cut -d. -f1)); \
		stats_filename="stats_r_$${r_val}_m_$${m_val}_c_$${c_val}_k_$${k_val}_y_$${y_val}_a_$${a_val}.txt"; \
		ad_stats_filename="ad_stats_r_$${r_val}_m_$${m_val}_c_$${c_val}_k_$${k_val}_y_$${y_val}_a_$${a_val}.txt"; \
		./$(BUILD_DIR)/$(TEST) $$params -w $$WORKER_ID > /dev/null 2>&1; \
		if [ -f "outputs_$${WORKER_ID}/stats.txt" ]; then \
			mv "outputs_$${WORKER_ID}/stats.txt" "$(BATCH_DIR)/$$stats_filename"; \
			#echo "   ✅ Saved stats.txt to $(BATCH_DIR)/$$stats_filename"; \
		else \
			echo "   ⚠️ Warning: stats.txt not found for $$params"; \
		fi; \
		if [ -f "outputs_$${WORKER_ID}/ad_stats.txt" ]; then \
			mv "outputs_$${WORKER_ID}/ad_stats.txt" "$(BATCH_DIR)/$$ad_stats_filename"; \
			#echo "   ✅ Saved ad_stats.txt to $(BATCH_DIR)/$$ad_stats_filename"; \
		else \
			echo "   ⚠️ Warning: ad_stats.txt not found for $$params"; \
		fi; \
		rm -rf outputs_$${WORKER_ID} inputs_$${WORKER_ID} archive_$${WORKER_ID} logs_$${WORKER_ID} 2>/dev/null; \
		' \
	; \
	end_time=$$(date +%s); \
	total_duration=$$((end_time - start_time)); \
	total_min=$$((total_duration / 60)); \
	total_sec=$$((total_duration % 60)); \
	echo ""; \
	echo "========================================"; \
	echo "✅ Adaptive parallel batch testing completed"; \
	echo "📊 Collected both stats.txt and ad_stats.txt files"; \
	echo "⏱️  Total time: $$total_min minutes $$total_sec seconds"; \
	echo "📁 Results saved in: $(BATCH_DIR)"

# Generate parameter combinations for grid search
# Usage: make generate-params OUTPUT=params.txt
generate-params:
	@if [ -z "$(OUTPUT)" ]; then \
		echo "❌ Please specify OUTPUT file"; \
		exit 1; \
	fi
	@echo "Generating parameter combinations to $(OUTPUT)"
	@> $(OUTPUT)
	@for res in 500 750 1000 1250 1500; do \
		for mature in 150 160 170 180 190; do \
			for cloud in 400 500 600 700; do \
				for ratio in 0.4 0.5 0.6 0.7; do \
					for ydist in 70000 80000 90000; do \
						for motion in 8 10 12; do \
							echo "-r $$res -m $$mature -c $$cloud -k $$ratio -y $$ydist -a $$motion" >> $(OUTPUT); \
						done; \
					done; \
				done; \
			done; \
		done; \
	done
	@echo "✅ Generated $$(wc -l < $(OUTPUT)) parameter combinations"

# Debug: Test parameter extraction
debug-params:
	@echo "Testing parameter extraction with sample line:"
	@echo "  -r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12"
	@echo ""
	@r_val=$$(echo "-r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12" | sed -n 's/.*-r \([0-9]*\).*/\1/p'); \
	m_val=$$(echo "-r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12" | sed -n 's/.*-m \([0-9]*\).*/\1/p'); \
	c_val=$$(echo "-r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12" | sed -n 's/.*-c \([0-9]*\).*/\1/p'); \
	k_val=$$(echo "-r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12" | sed -n 's/.*-k \([0-9.]*\).*/\1/p'); \
	y_val=$$(echo "-r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12" | sed -n 's/.*-y \([0-9]*\).*/\1/p'); \
	a_val=$$(echo "-r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12" | sed -n 's/.*-a \([0-9.]*\).*/\1/p'); \
	echo "Extracted values:"; \
	echo "  r_val = $$r_val"; \
	echo "  m_val = $$m_val"; \
	echo "  c_val = $$c_val"; \
	echo "  k_val = $$k_val"; \
	echo "  y_val = $$y_val"; \
	echo "  a_val = $$a_val"; \
	echo ""; \
	if [ -z "$$k_val" ]; then k_val="000"; else k_val=$$(printf "%03d" $$(echo "$$k_val * 100" | bc | cut -d. -f1)); fi; \
	if [ -z "$$a_val" ]; then a_val="00"; else a_val=$$(printf "%02d" $$(echo "$$a_val + 0.5" | bc | cut -d. -f1)); fi; \
	echo "Formatted values:"; \
	echo "  k_val = $$k_val (after multiplying by 100 and formatting)"; \
	echo "  a_val = $$a_val (after rounding)"; \
	echo ""; \
	stats_filename="stats_r_$${r_val}_m_$${m_val}_c_$${c_val}_k_$${k_val}_y_$${y_val}_a_$${a_val}.txt"; \
	ad_stats_filename="ad_stats_r_$${r_val}_m_$${m_val}_c_$${c_val}_k_$${k_val}_y_$${y_val}_a_$${a_val}.txt"; \
	echo "Final filenames:"; \
	echo "  $$stats_filename"; \
	echo "  $$ad_stats_filename"

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
	rm -rf $(BUILD_DIR)/* $(TARGET) batch_test_*

.PHONY: all clean run tests test progress build-test run-test quick-test batch-test parallel-batch-test adaptive-parallel-batch-test generate-params debug-params

# Help target
help:
	@echo "Available commands:"
	@echo ""
	@echo "=== Basic Testing ==="
	@echo "  make test                       - List and run tests interactively"
	@echo "  make test TEST=test_cl          - Build and run test_cl once"
	@echo "  make tests                      - Build and run all tests"
	@echo ""
	@echo "=== Direct Compilation (for batch testing) ==="
	@echo "  make build-test TEST=test_cl    - Build test executable once"
	@echo "  make run-test TEST=test_cl ARGS='...' - Run built test with args"
	@echo "  make quick-test TEST=test_cl ARGS='...' - Build and run in one step"
	@echo ""
	@echo "=== Batch Testing ==="
	@echo "  make batch-test TEST=test_cl PARAM_FILE=file.txt - Run from parameter file (serial)"
	@echo "  make parallel-batch-test TEST=test_cl PARAM_FILE=file.txt CORES=8 - Run in parallel"
	@echo "  make adaptive-parallel-batch-test TEST=test_cl PARAM_FILE=file.txt CORES=8 - Run in parallel and collect ad_stats.txt"
	@echo "  make generate-params OUTPUT=file.txt - Generate parameter combinations"
	@echo "  make debug-params               - Test parameter extraction"
	@echo ""
	@echo "Examples:"
	@echo "  make test TEST=test_cl"
	@echo "  make quick-test TEST=test_cl ARGS='-r 500 -m 180'"
	@echo "  make batch-test TEST=test_cl PARAM_FILE=my_params.txt"
	@echo "  make parallel-batch-test TEST=test_cl PARAM_FILE=my_params.txt CORES=8"
	@echo "  make adaptive-parallel-batch-test TEST=test_cl PARAM_FILE=my_params.txt CORES=8"
	@echo ""
	@echo "Parameter file format (my_params.txt):"
	@echo "  -r 500 -m 170 -c 600 -k 0.7 -y 75000 -a 12"
	@echo "  -r 1000 -m 180 -c 500 -k 0.5 -y 80000 -a 10"
	@echo ""
	@echo "Batch test output:"
	@echo "  Results saved in: batch_test_YYYYMMDD_HHMMSS/"
	@echo "  File format: stats_r_XXXX_m_XXX_c_XXXX_k_XXX_y_XXXXXX_a_XX.txt"
	@echo "  Adaptive format: ad_stats_r_XXXX_m_XXX_c_XXXX_k_XXX_y_XXXXXX_a_XX.txt"
