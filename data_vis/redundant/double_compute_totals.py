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
    double stats_discrepancy;   // True - Measured for regular stats
    double ad_stats_discrepancy; // True - Measured for AD stats
    int stats_scan_count;
    int ad_stats_scan_count;
} TestResult;

// Extract parameters from filename (handles both stats and ad_stats)
int extract_parameters(const char* filename, TestResult* result) {
    regex_t regex;
    regmatch_t matches[10];
    
    const char* pattern = "^(ad_)?stats_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt$";
    
    if (regcomp(&regex, pattern, REG_EXTENDED) != 0) {
        fprintf(stderr, "Failed to compile regex\n");
        return -1;
    }
    
    if (regexec(&regex, filename, 10, matches, 0) == 0) {
        char buffer[32];
        
        // Check if it's ad_stats (match 1 contains "ad_" or NULL)
        int is_ad = (matches[1].rm_so != -1 && matches[1].rm_so != matches[1].rm_eo);
        
        // Extract each parameter (matches start at index 2)
        int idx = 2;
        
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
        
        regfree(&regex);
        
        // Set the filename type in the result
        if (is_ad) {
            strcpy(result->filename_type, "ad_stats");
        } else {
            strcpy(result->filename_type, "stats");
        }
        
        return 0;
    }
    
    regfree(&regex);
    return -1;
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
        results[*count].stats_discrepancy = NAN;
        results[*count].ad_stats_discrepancy = NAN;
        results[*count].stats_scan_count = 0;
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
    int stats_files_processed = 0;
    int ad_stats_files_processed = 0;
    
    // Open directory
    dir = opendir(folder_path);
    if (!dir) {
        fprintf(stderr, "❌ Cannot open directory: %s\n", folder_path);
        return -1;
    }
    
    printf("=========================================\n");
    printf("  RAINFALL ACCUMULATION DISCREPANCY\n");
    printf("=========================================\n");
    printf("Processing folder: %s\n\n", folder_path);
    
    // Initialize results array
    for (int i = 0; i < MAX_RESULTS; i++) {
        results[i].stats_discrepancy = NAN;
        results[i].ad_stats_discrepancy = NAN;
        results[i].stats_scan_count = 0;
        results[i].ad_stats_scan_count = 0;
    }
    
    // Process each file
    while ((entry = readdir(dir)) != NULL) {
        // Check if it's a stats file (regular or AD)
        if (strstr(entry->d_name, "stats_x1_") != entry->d_name && 
            strstr(entry->d_name, "ad_stats_x1_") != entry->d_name) {
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
        result.stats_discrepancy = NAN;
        result.ad_stats_discrepancy = NAN;
        
        if (extract_parameters(entry->d_name, &result) != 0) {
            fprintf(stderr, "  ⚠️ Skipping: %s (cannot parse filename)\n", entry->d_name);
            continue;
        }
        
        // Read stats file and compute discrepancy
        double discrepancy = 0.0;
        int scan_count = 0;
        
        if (read_stats_file(filepath, &discrepancy, &scan_count) != 0) {
            fprintf(stderr, "  ⚠️ Skipping: %s (cannot read file)\n", entry->d_name);
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
                
                printf("[AD %d] %s\n", ad_stats_files_processed, entry->d_name);
                printf("    Parameters: x1=%d x2=%d x3=%d x4=%d x5=%d x6=%d x7=%d\n", 
                       result.x1, result.x2, result.x3, result.x4, result.x5, result.x6, result.x7);
                printf("    Scans: %d\n", scan_count);
                printf("    Discrepancy (True - Measured): %.10f\n\n", discrepancy);
            } else {
                result_entry->stats_discrepancy = discrepancy;
                result_entry->stats_scan_count = scan_count;
                stats_files_processed++;
                
                printf("[STATS %d] %s\n", stats_files_processed, entry->d_name);
                printf("    Parameters: x1=%d x2=%d x3=%d x4=%d x5=%d x6=%d x7=%d\n", 
                       result.x1, result.x2, result.x3, result.x4, result.x5, result.x6, result.x7);
                printf("    Scans: %d\n", scan_count);
                printf("    Discrepancy (True - Measured): %.10f\n\n", discrepancy);
            }
        }
    }
    
    closedir(dir);
    
    if (result_count == 0) {
        printf("❌ No valid stats files found\n");
        return -1;
    }
    
    // Sort results
    qsort(results, result_count, sizeof(TestResult), compare_results);
    
    // Save results to file
    char output_file[MAX_FILENAME];
    snprintf(output_file, sizeof(output_file), "%s/total_accumulation_results.txt", folder_path);
    
    FILE* out = fopen(output_file, "w");
    if (!out) {
        fprintf(stderr, "❌ Cannot create output file: %s\n", output_file);
        return -1;
    }
    
    fprintf(out, "# Total Rainfall Accumulation Discrepancy Results\n");
    fprintf(out, "# Generated: %s %s\n", __DATE__, __TIME__);
    fprintf(out, "# Format: x1 x2 x3 x4 x5 x6 x7 Stats_Discrepancy AD_Stats_Discrepancy\n");
    fprintf(out, "# Total parameter sets: %d\n", result_count);
    fprintf(out, "# Stats files processed: %d\n", stats_files_processed);
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
    fprintf(out, "#   Stats_Discrepancy - Sum(True) - Sum(Measured) for regular stats\n");
    fprintf(out, "#   AD_Stats_Discrepancy - Sum(True) - Sum(Measured) for AD stats\n");
    fprintf(out, "#   Positive value means true accumulation > measured accumulation\n");
    fprintf(out, "#   Negative value means measured accumulation > true accumulation\n");
    fprintf(out, "#\n");
    
    // Write results in the same format as EMD output
    for (int i = 0; i < result_count; i++) {
        fprintf(out, "%d %d %d %d %d %d %d %.10f %.10f\n",
                results[i].x1, results[i].x2, results[i].x3,
                results[i].x4, results[i].x5, results[i].x6,
                results[i].x7, 
                results[i].stats_discrepancy, 
                results[i].ad_stats_discrepancy);
    }
    
    fclose(out);
    
    // Calculate statistics
    double sum_stats_disc = 0.0;
    double sum_ad_stats_disc = 0.0;
    int stats_valid = 0;
    int ad_stats_valid = 0;
    
    for (int i = 0; i < result_count; i++) {
        if (!isnan(results[i].stats_discrepancy)) {
            sum_stats_disc += results[i].stats_discrepancy;
            stats_valid++;
        }
        if (!isnan(results[i].ad_stats_discrepancy)) {
            sum_ad_stats_disc += results[i].ad_stats_discrepancy;
            ad_stats_valid++;
        }
    }
    
    // Print summary
    printf("=========================================\n");
    printf("✅ Complete!\n");
    printf("📁 Results saved to: %s\n", output_file);
    printf("\n");
    printf("Summary:\n");
    printf("  Total parameter sets: %d\n", result_count);
    printf("  Stats files processed: %d\n", stats_files_processed);
    printf("  AD Stats files processed: %d\n", ad_stats_files_processed);
    printf("\n");
    
    if (stats_valid > 0) {
        printf("  Regular Stats Discrepancy (True - Measured):\n");
        printf("    Valid values: %d\n", stats_valid);
        printf("    Mean: %.10f\n", sum_stats_disc / stats_valid);
        printf("    Sum:  %.10f\n", sum_stats_disc);
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
