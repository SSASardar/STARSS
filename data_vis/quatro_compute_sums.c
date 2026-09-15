#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <dirent.h>
#include <sys/stat.h>
#include <regex.h>

#define MAX_FILENAME 512
#define MAX_LINE 1024
#define MAX_SCANS 1000
#define MAX_RESULTS 10000

// Structure to hold parameters from filename
typedef struct {
    int x1;  // radius of raincell (km) - multiplied by 100
    int x2;  // core ratio (0-1) - multiplied by 100
    int x3;  // rain intensity (mm/hr)
    int x4;  // apparent motion (m/s) - multiplied by 10
    int x5;  // cloud base height (km) - multiplied by 10
    int x6;  // distance to C-band radar (km)
    int x7;  // storm duration (minutes)
    double x_stats_discrepancy;      // True - Measured for X-band stats
    double c_stats_discrepancy;      // True - Measured for C-band stats
    double combi_stats_discrepancy;  // True - Measured for combi stats
    double ad_stats_discrepancy;     // True - Measured for AD stats
    int x_stats_scan_count;
    int c_stats_scan_count;
    int combi_stats_scan_count;
    int ad_stats_scan_count;
    char filename_type[20];     // "x_stats", "c_stats", "combi_stats", or "ad_stats"
} TestResult;

// Extract parameters from filename (handles x_stats, c_stats, combi_stats, and ad_stats)
int extract_parameters(const char* filename, TestResult* result) {
    regex_t regex;
    regmatch_t matches[10];
    
    // Try ad_stats pattern first (no C_ in name)
    const char* ad_pattern = "^ad_stats_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt$";
    // Combi stats pattern
    const char* combi_pattern = "^combi_stats_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt$";
    // Regular C stats pattern (with C_)
    const char* c_stats_pattern = "^stats_C_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt$";
    // Regular X stats pattern (with X_)
    const char* x_stats_pattern = "^stats_X_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt$";
    
    int file_type = 0; // 0=unknown, 1=ad_stats, 2=combi_stats, 3=c_stats, 4=x_stats
    int matched = 0;
    
    // Try ad_stats pattern first
    if (regcomp(&regex, ad_pattern, REG_EXTENDED) != 0) {
        fprintf(stderr, "Failed to compile ad_stats regex\n");
        return -1;
    }
    if (regexec(&regex, filename, 10, matches, 0) == 0) {
        file_type = 1; // ad_stats
        matched = 1;
    }
    regfree(&regex);
    
    // If not ad_stats, try combi_stats pattern
    if (!matched) {
        if (regcomp(&regex, combi_pattern, REG_EXTENDED) != 0) {
            fprintf(stderr, "Failed to compile combi_stats regex\n");
            return -1;
        }
        if (regexec(&regex, filename, 10, matches, 0) == 0) {
            file_type = 2; // combi_stats
            matched = 1;
        }
        regfree(&regex);
    }
    
    // If not combi_stats, try C stats pattern
    if (!matched) {
        if (regcomp(&regex, c_stats_pattern, REG_EXTENDED) != 0) {
            fprintf(stderr, "Failed to compile c_stats regex\n");
            return -1;
        }
        if (regexec(&regex, filename, 10, matches, 0) == 0) {
            file_type = 3; // c_stats
            matched = 1;
        }
        regfree(&regex);
    }
    
    // If not C stats, try X stats pattern
    if (!matched) {
        if (regcomp(&regex, x_stats_pattern, REG_EXTENDED) != 0) {
            fprintf(stderr, "Failed to compile x_stats regex\n");
            return -1;
        }
        if (regexec(&regex, filename, 10, matches, 0) == 0) {
            file_type = 4; // x_stats
            matched = 1;
        }
        regfree(&regex);
    }
    
    if (!matched) {
        return -1;
    }
    
    // Extract each parameter (matches start at index 1)
    char buffer[32];
    int idx = 1;
    
    int len = matches[idx].rm_eo - matches[idx].rm_so;
    snprintf(buffer, len + 1, "%.*s", len, filename + matches[idx].rm_so);
    result->x1 = atoi(buffer);
    idx++;
    
    len = matches[idx].rm_eo - matches[idx].rm_so;
    snprintf(buffer, len + 1, "%.*s", len, filename + matches[idx].rm_so);
    result->x2 = atoi(buffer);
    idx++;
    
    len = matches[idx].rm_eo - matches[idx].rm_so;
    snprintf(buffer, len + 1, "%.*s", len, filename + matches[idx].rm_so);
    result->x3 = atoi(buffer);
    idx++;
    
    len = matches[idx].rm_eo - matches[idx].rm_so;
    snprintf(buffer, len + 1, "%.*s", len, filename + matches[idx].rm_so);
    result->x4 = atoi(buffer);
    idx++;
    
    len = matches[idx].rm_eo - matches[idx].rm_so;
    snprintf(buffer, len + 1, "%.*s", len, filename + matches[idx].rm_so);
    result->x5 = atoi(buffer);
    idx++;
    
    len = matches[idx].rm_eo - matches[idx].rm_so;
    snprintf(buffer, len + 1, "%.*s", len, filename + matches[idx].rm_so);
    result->x6 = atoi(buffer);
    idx++;
    
    len = matches[idx].rm_eo - matches[idx].rm_so;
    snprintf(buffer, len + 1, "%.*s", len, filename + matches[idx].rm_so);
    result->x7 = atoi(buffer);
    
    // Set the filename type in the result
    switch (file_type) {
        case 1: strcpy(result->filename_type, "ad_stats"); break;
        case 2: strcpy(result->filename_type, "combi_stats"); break;
        case 3: strcpy(result->filename_type, "c_stats"); break;
        case 4: strcpy(result->filename_type, "x_stats"); break;
        default: strcpy(result->filename_type, "unknown"); break;
    }
    
    return 0;
}

// Read stats file and compute discrepancy (True - Measured) from columns 7 and 8
int read_stats_file(const char* filename, double* discrepancy, int* scan_count) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        return -1;
    }
    
    char line[MAX_LINE];
    int count = 0;
    double sum_meas = 0.0;
    double sum_true = 0.0;
    
    // Skip header
    if (fgets(line, sizeof(line), file) == NULL) {
        fclose(file);
        return -1;
    }
    
    // Read data lines
    while (fgets(line, sizeof(line), file) != NULL) {
        int scan_idx;
        double mse, mae, bias, total_meas_row, total_true_row;
        double total_meas_mm2_row, total_true_mm2_row;
        
        if (sscanf(line, "%d %lf %lf %lf %lf %lf %lf %lf",
                   &scan_idx, &mse, &mae, &bias, 
                   &total_meas_row, &total_true_row, 
                   &total_meas_mm2_row, &total_true_mm2_row) == 8) {
            
            // Sum columns 7 and 8 (total_meas_mm2 and total_true_mm2)
            sum_meas += total_meas_mm2_row;
            sum_true += total_true_mm2_row;
            count++;
        }
    }
    
    fclose(file);
    
    if (count == 0) {
        return -1;
    }
    
    // Compute discrepancy: True - Measured
    *discrepancy = sum_true - sum_meas;
    *scan_count = count;
    
    return 0;
}

// Compare function for qsort
int compare_results(const void* a, const void* b) {
    TestResult* result_a = (TestResult*)a;
    TestResult* result_b = (TestResult*)b;
    
    // Sort by x1 (core size) then x2 (core ratio) etc.
    if (result_a->x1 != result_b->x1) return result_a->x1 - result_b->x1;
    if (result_a->x2 != result_b->x2) return result_a->x2 - result_b->x2;
    if (result_a->x3 != result_b->x3) return result_a->x3 - result_b->x3;
    if (result_a->x4 != result_b->x4) return result_a->x4 - result_b->x4;
    if (result_a->x5 != result_b->x5) return result_a->x5 - result_b->x5;
    if (result_a->x6 != result_b->x6) return result_a->x6 - result_b->x6;
    return result_a->x7 - result_b->x7;
}

// Find or create result entry in array
TestResult* find_or_create_result(TestResult* results, int* count, TestResult* new_result) {
    // Search for matching parameters
    for (int i = 0; i < *count; i++) {
        if (results[i].x1 == new_result->x1 &&
            results[i].x2 == new_result->x2 &&
            results[i].x3 == new_result->x3 &&
            results[i].x4 == new_result->x4 &&
            results[i].x5 == new_result->x5 &&
            results[i].x6 == new_result->x6 &&
            results[i].x7 == new_result->x7) {
            return &results[i];
        }
    }
    
    // Not found, add new entry
    if (*count < MAX_RESULTS) {
        results[*count] = *new_result;
        results[*count].x_stats_discrepancy = NAN;
        results[*count].c_stats_discrepancy = NAN;
        results[*count].combi_stats_discrepancy = NAN;
        results[*count].ad_stats_discrepancy = NAN;
        results[*count].x_stats_scan_count = 0;
        results[*count].c_stats_scan_count = 0;
        results[*count].combi_stats_scan_count = 0;
        results[*count].ad_stats_scan_count = 0;
        (*count)++;
        return &results[*count - 1];
    }
    
    return NULL;
}

// Main function to process all stats files in a directory
int process_batch_folder(const char* folder_path) {
    DIR* dir;
    struct dirent* entry;
    struct stat statbuf;
    char filepath[MAX_FILENAME];
    TestResult results[MAX_RESULTS];
    int result_count = 0;
    int x_stats_files_processed = 0;
    int c_stats_files_processed = 0;
    int combi_stats_files_processed = 0;
    int ad_stats_files_processed = 0;
    
    // Open directory
    dir = opendir(folder_path);
    if (!dir) {
        fprintf(stderr, "Cannot open directory: %s\n", folder_path);
        return -1;
    }
    
    printf("=========================================\n");
    printf("  RAINFALL ACCUMULATION DISCREPANCY\n");
    printf("=========================================\n");
    printf("Processing folder: %s\n\n", folder_path);
    
    // Initialize results array
    for (int i = 0; i < MAX_RESULTS; i++) {
        results[i].x_stats_discrepancy = NAN;
        results[i].c_stats_discrepancy = NAN;
        results[i].combi_stats_discrepancy = NAN;
        results[i].ad_stats_discrepancy = NAN;
        results[i].x_stats_scan_count = 0;
        results[i].c_stats_scan_count = 0;
        results[i].combi_stats_scan_count = 0;
        results[i].ad_stats_scan_count = 0;
        results[i].filename_type[0] = '\0';
    }
    
    // Process each file
    while ((entry = readdir(dir)) != NULL) {
        // Check if it's one of our stats files
        if (strncmp(entry->d_name, "stats_X_x1_", 11) != 0 && 
            strncmp(entry->d_name, "stats_C_x1_", 11) != 0 && 
            strncmp(entry->d_name, "combi_stats_x1_", 15) != 0 && 
            strncmp(entry->d_name, "ad_stats_x1_", 12) != 0) {
            continue;
        }
        
        snprintf(filepath, sizeof(filepath), "%s/%s", folder_path, entry->d_name);
        
        // Get file stats
        if (stat(filepath, &statbuf) != 0) {
            continue;
        }
        
        // Extract parameters from filename
        TestResult result;
        memset(&result, 0, sizeof(TestResult));
        result.x_stats_discrepancy = NAN;
        result.c_stats_discrepancy = NAN;
        result.combi_stats_discrepancy = NAN;
        result.ad_stats_discrepancy = NAN;
        result.filename_type[0] = '\0';
        
        if (extract_parameters(entry->d_name, &result) != 0) {
            fprintf(stderr, "  Skipping: %s (cannot parse filename)\n", entry->d_name);
            continue;
        }
        
        // Read stats file and compute discrepancy
        double discrepancy = 0.0;
        int scan_count = 0;
        
        if (read_stats_file(filepath, &discrepancy, &scan_count) != 0) {
            fprintf(stderr, "  Skipping: %s (cannot read file)\n", entry->d_name);
            continue;
        }
        
        // Find or create result entry
        TestResult* result_entry = find_or_create_result(results, &result_count, &result);
        
        if (result_entry) {
            // Store discrepancy in appropriate field based on file type
            if (strcmp(result.filename_type, "ad_stats") == 0) {
                result_entry->ad_stats_discrepancy = discrepancy;
                result_entry->ad_stats_scan_count = scan_count;
                ad_stats_files_processed++;
            } else if (strcmp(result.filename_type, "combi_stats") == 0) {
                result_entry->combi_stats_discrepancy = discrepancy;
                result_entry->combi_stats_scan_count = scan_count;
                combi_stats_files_processed++;
            } else if (strcmp(result.filename_type, "c_stats") == 0) {
                result_entry->c_stats_discrepancy = discrepancy;
                result_entry->c_stats_scan_count = scan_count;
                c_stats_files_processed++;
            } else if (strcmp(result.filename_type, "x_stats") == 0) {
                result_entry->x_stats_discrepancy = discrepancy;
                result_entry->x_stats_scan_count = scan_count;
                x_stats_files_processed++;
            }
        }
    }
    
    closedir(dir);
    
    if (result_count == 0) {
        printf("No valid stats files found\n");
        return -1;
    }
    
    // Sort results
    qsort(results, result_count, sizeof(TestResult), compare_results);
    
    // Save results to file
    char output_file[MAX_FILENAME];
    snprintf(output_file, sizeof(output_file), "%s/results_sums.txt", folder_path);
    
    FILE* out = fopen(output_file, "w");
    if (!out) {
        fprintf(stderr, "Cannot create output file: %s\n", output_file);
        return -1;
    }
    
    fprintf(out, "# Total Rainfall Accumulation Discrepancy Results\n");
    fprintf(out, "# Generated: %s %s\n", __DATE__, __TIME__);
    fprintf(out, "# Format: x1 x2 x3 x4 x5 x6 x7 X_Stats C_Stats Combi_Stats AD_Stats\n");
    fprintf(out, "# Total parameter sets: %d\n", result_count);
    fprintf(out, "# X Stats files processed: %d\n", x_stats_files_processed);
    fprintf(out, "# C Stats files processed: %d\n", c_stats_files_processed);
    fprintf(out, "# Combi Stats files processed: %d\n", combi_stats_files_processed);
    fprintf(out, "# AD Stats files processed: %d\n", ad_stats_files_processed);
    fprintf(out, "#\n");
    fprintf(out, "# Column descriptions:\n");
    fprintf(out, "#   x1 - radius of raincell (km) * 100\n");
    fprintf(out, "#   x2 - core ratio (0-1) * 100\n");
    fprintf(out, "#   x3 - rain intensity (mm/hr)\n");
    fprintf(out, "#   x4 - apparent motion (m/s) * 10\n");
    fprintf(out, "#   x5 - cloud base height (km) * 10\n");
    fprintf(out, "#   x6 - distance to C-band radar (km)\n");
    fprintf(out, "#   x7 - storm duration (minutes)\n");
    fprintf(out, "#   X_Stats_Discrepancy - Sum(True) - Sum(Measured) for X-band stats\n");
    fprintf(out, "#   C_Stats_Discrepancy - Sum(True) - Sum(Measured) for C-band stats\n");
    fprintf(out, "#   Combi_Stats_Discrepancy - Sum(True) - Sum(Measured) for combi stats\n");
    fprintf(out, "#   AD_Stats_Discrepancy - Sum(True) - Sum(Measured) for AD stats\n");
    fprintf(out, "#   Positive value means true accumulation > measured accumulation\n");
    fprintf(out, "#   Negative value means measured accumulation > true accumulation\n");
    fprintf(out, "#\n");
    
    // Write results in the specified column order: X, C, combi, ad
    for (int i = 0; i < result_count; i++) {
        fprintf(out, "%d %d %d %d %d %d %d %.10f %.10f %.10f %.10f\n",
                results[i].x1, results[i].x2, results[i].x3,
                results[i].x4, results[i].x5, results[i].x6,
                results[i].x7, 
                results[i].x_stats_discrepancy,
                results[i].c_stats_discrepancy,
                results[i].combi_stats_discrepancy,
                results[i].ad_stats_discrepancy);
    }
    
    fclose(out);
    
    // Calculate statistics for each type
    double sum_x_stats_disc = 0.0;
    double sum_c_stats_disc = 0.0;
    double sum_combi_stats_disc = 0.0;
    double sum_ad_stats_disc = 0.0;
    int x_stats_valid = 0;
    int c_stats_valid = 0;
    int combi_stats_valid = 0;
    int ad_stats_valid = 0;
    
    for (int i = 0; i < result_count; i++) {
        if (!isnan(results[i].x_stats_discrepancy)) {
            sum_x_stats_disc += results[i].x_stats_discrepancy;
            x_stats_valid++;
        }
        if (!isnan(results[i].c_stats_discrepancy)) {
            sum_c_stats_disc += results[i].c_stats_discrepancy;
            c_stats_valid++;
        }
        if (!isnan(results[i].combi_stats_discrepancy)) {
            sum_combi_stats_disc += results[i].combi_stats_discrepancy;
            combi_stats_valid++;
        }
        if (!isnan(results[i].ad_stats_discrepancy)) {
            sum_ad_stats_disc += results[i].ad_stats_discrepancy;
            ad_stats_valid++;
        }
    }
    
    // Print summary
    printf("=========================================\n");
    printf("Complete!\n");
    printf("Results saved to: %s\n", output_file);
    printf("\n");
    printf("Summary:\n");
    printf("  Total parameter sets: %d\n", result_count);
    printf("  X Stats files processed: %d\n", x_stats_files_processed);
    printf("  C Stats files processed: %d\n", c_stats_files_processed);
    printf("  Combi Stats files processed: %d\n", combi_stats_files_processed);
    printf("  AD Stats files processed: %d\n", ad_stats_files_processed);
    printf("\n");
    
    if (x_stats_valid > 0) {
        printf("  X Stats Discrepancy (True - Measured):\n");
        printf("    Valid values: %d\n", x_stats_valid);
        printf("    Mean: %.10f\n", sum_x_stats_disc / x_stats_valid);
        printf("    Sum:  %.10f\n", sum_x_stats_disc);
    }
    
    if (c_stats_valid > 0) {
        printf("\n  C Stats Discrepancy (True - Measured):\n");
        printf("    Valid values: %d\n", c_stats_valid);
        printf("    Mean: %.10f\n", sum_c_stats_disc / c_stats_valid);
        printf("    Sum:  %.10f\n", sum_c_stats_disc);
    }
    
    if (combi_stats_valid > 0) {
        printf("\n  Combi Stats Discrepancy (True - Measured):\n");
        printf("    Valid values: %d\n", combi_stats_valid);
        printf("    Mean: %.10f\n", sum_combi_stats_disc / combi_stats_valid);
        printf("    Sum:  %.10f\n", sum_combi_stats_disc);
    }
    
    if (ad_stats_valid > 0) {
        printf("\n  AD Stats Discrepancy (True - Measured):\n");
        printf("    Valid values: %d\n", ad_stats_valid);
        printf("    Mean: %.10f\n", sum_ad_stats_disc / ad_stats_valid);
        printf("    Sum:  %.10f\n", sum_ad_stats_disc);
    }
    printf("=========================================\n");
    
    return 0;
}

// Main function
int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <batch_folder>\n", argv[0]);
        fprintf(stderr, "Example: %s batch_test_20260506_155323\n", argv[0]);
        return 1;
    }
    
    return process_batch_folder(argv[1]);
}
