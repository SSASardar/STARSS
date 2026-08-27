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
    double emd;           // EMD for regular stats
    double ad_emd;        // EMD for AD stats
    char filename_type[20]; // "stats" or "ad_stats"
} TestResult;

// Structure to hold histogram data
typedef struct {
    double* values;
    int count;
} Histogram;

// Extract parameters from filename (handles both stats and ad_stats)
int extract_parameters(const char* filename, TestResult* result) {
    regex_t regex;
    regmatch_t matches[10];  // Increased size to accommodate all groups
    
    // Pattern for stats: stats_x1_(\d+)_x2_(\d+)_x3_(\d+)_x4_(\d+)_x5_(\d+)_x6_(\d+)_x7_(\d+)\.txt
    // Pattern for ad_stats: ad_stats_x1_(\d+)_x2_(\d+)_x3_(\d+)_x4_(\d+)_x5_(\d+)_x6_(\d+)_x7_(\d+)\.txt
    const char* pattern = "^(ad_)?stats_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt$";
    
    if (regcomp(&regex, pattern, REG_EXTENDED) != 0) {
        fprintf(stderr, "Failed to compile regex\n");
        return -1;
    }
    
    if (regexec(&regex, filename, 10, matches, 0) == 0) {
        char buffer[32];
        
        // Check if it's ad_stats (match 1 contains "ad_" or NULL)
        if (matches[1].rm_so != -1 && matches[1].rm_so != matches[1].rm_eo) {
            strcpy(result->filename_type, "ad_stats");
        } else {
            strcpy(result->filename_type, "stats");
        }
        
        // Extract each parameter (matches start at index 2 because group 1 is optional)
        int idx = 2;  // Start from group 2 (first parameter after optional group)
        
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
        return 0;
    }
    
    regfree(&regex);
    return -1;
}

// Read stats file and extract measured and true rainfall rates
int read_stats_file(const char* filename, double** measured, double** true_values, int* count) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        return -1;
    }
    
    char line[MAX_LINE];
    int line_num = 0;
    double* meas = NULL;
    double* truth = NULL;
    int capacity = 10;
    int size = 0;
    
    meas = (double*)malloc(capacity * sizeof(double));
    truth = (double*)malloc(capacity * sizeof(double));
    
    if (!meas || !truth) {
        fclose(file);
        free(meas);
        free(truth);
        return -1;
    }
    
    // Skip header
    if (fgets(line, sizeof(line), file) == NULL) {
        fclose(file);
        free(meas);
        free(truth);
        return -1;
    }
    
    // Read data lines
    while (fgets(line, sizeof(line), file) != NULL) {
        // Format: scan_idx mse mae bias total_meas total_true total_meas_mm2 total_true_mm2
        int scan_idx;
        double mse, mae, bias, total_meas, total_true, total_meas_mm2, total_true_mm2;
        
        if (sscanf(line, "%d %lf %lf %lf %lf %lf %lf %lf",
                   &scan_idx, &mse, &mae, &bias, 
                   &total_meas, &total_true, 
                   &total_meas_mm2, &total_true_mm2) == 8) {
            
            // Resize if needed
            if (size >= capacity) {
                capacity *= 2;
                meas = (double*)realloc(meas, capacity * sizeof(double));
                truth = (double*)realloc(truth, capacity * sizeof(double));
                if (!meas || !truth) {
                    fclose(file);
                    free(meas);
                    free(truth);
                    return -1;
                }
            }
            
            meas[size] = total_meas_mm2;
            truth[size] = total_true_mm2;
            size++;
        }
    }
    
    fclose(file);
    
    if (size == 0) {
        free(meas);
        free(truth);
        return -1;
    }
    
    *measured = meas;
    *true_values = truth;
    *count = size;
    
    return 0;
}

// Normalize histogram (convert to probability distribution)
void normalize_histogram(double* values, int count, double** normalized, int* norm_count) {
    double sum = 0.0;
    
    for (int i = 0; i < count; i++) {
        sum += values[i];
    }
    
    if (sum == 0.0) {
        *normalized = NULL;
        *norm_count = 0;
        return;
    }
    
    double* norm = (double*)malloc(count * sizeof(double));
    if (!norm) {
        *normalized = NULL;
        *norm_count = 0;
        return;
    }
    
    for (int i = 0; i < count; i++) {
        norm[i] = values[i] / sum;
    }
    
    *normalized = norm;
    *norm_count = count;
}

// Compute Earth Mover's Distance (1D Wasserstein distance)
double compute_emd_with_positions(double* dist1, double* dist2, int count) {
    // EMD = integral of |CDF1 - CDF2| dx
    // For discrete distributions with positions 0,1,2,...,n-1
    
    if (count == 0) {
        return NAN;
    }
    
    double cum1 = 0.0;
    double cum2 = 0.0;
    double emd = 0.0;
    
    for (int i = 0; i < count; i++) {
        cum1 += dist1[i];
        cum2 += dist2[i];
        emd += fabs(cum1 - cum2);
    }
    
    return emd / count;
}

// Compare function for qsort
int compare_results(const void* a, const void* b) {
    TestResult* result_a = (TestResult*)a;
    TestResult* result_b = (TestResult*)b;
    
    // Sort primarily by regular EMD
    if (result_a->emd < result_b->emd) return -1;
    if (result_a->emd > result_b->emd) return 1;
    
    // If regular EMD equal, sort by AD EMD
    if (result_a->ad_emd < result_b->ad_emd) return -1;
    if (result_a->ad_emd > result_b->ad_emd) return 1;
    
    return 0;
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
        results[*count].emd = NAN;
        results[*count].ad_emd = NAN;
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
    printf("  EARTH MOVER'S DISTANCE COMPUTATION (C)\n");
    printf("=========================================\n");
    printf("Processing folder: %s\n\n", folder_path);
    
    // Initialize results array
    for (int i = 0; i < MAX_RESULTS; i++) {
        results[i].emd = NAN;
        results[i].ad_emd = NAN;
        results[i].filename_type[0] = '\0';
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
        result.emd = NAN;
        result.ad_emd = NAN;
        
        if (extract_parameters(entry->d_name, &result) != 0) {
            fprintf(stderr, "  ⚠️ Skipping: %s (cannot parse filename)\n", entry->d_name);
            continue;
        }
        
        // Read stats file
        double* measured = NULL;
        double* true_values = NULL;
        int scan_count = 0;
        
        if (read_stats_file(filepath, &measured, &true_values, &scan_count) != 0) {
            fprintf(stderr, "  ⚠️ Skipping: %s (cannot read file)\n", entry->d_name);
            continue;
        }
        
        // Normalize histograms
        double* norm_measured = NULL;
        double* norm_true = NULL;
        int norm_count_meas = 0;
        int norm_count_true = 0;
        
        normalize_histogram(measured, scan_count, &norm_measured, &norm_count_meas);
        normalize_histogram(true_values, scan_count, &norm_true, &norm_count_true);
        
        // Find or create result entry
        TestResult* result_entry = find_or_create_result(results, &result_count, &result);
        
        if (norm_measured && norm_true && norm_count_meas == norm_count_true && result_entry) {
            // Compute EMD
            double emd_value = compute_emd_with_positions(norm_measured, norm_true, norm_count_meas);
            
            // Store in appropriate field based on file type
            if (strcmp(result.filename_type, "ad_stats") == 0) {
                result_entry->ad_emd = emd_value;
                ad_stats_files_processed++;
//                printf("[AD %d] %s\n", ad_stats_files_processed, entry->d_name);
//                printf("    Parameters: x1=%d x2=%d x3=%d x4=%d x5=%d x6=%d x7=%d\n", 
//                       result.x1, result.x2, result.x3, result.x4, result.x5, result.x6, result.x7);
//                printf("    Scans: %d\n", scan_count);
//                printf("    AD EMD: %.10f\n\n", emd_value);
            } else {
                result_entry->emd = emd_value;
                stats_files_processed++;
//                printf("[STATS %d] %s\n", stats_files_processed, entry->d_name);
//                printf("    Parameters: x1=%d x2=%d x3=%d x4=%d x5=%d x6=%d x7=%d\n", 
//                       result.x1, result.x2, result.x3, result.x4, result.x5, result.x6, result.x7);
//                printf("    Scans: %d\n", scan_count);
//                printf("    EMD: %.10f\n\n", emd_value);
            }
        } else {
            printf("[%s] %s\n", result.filename_type, entry->d_name);
            printf("    ⚠️ Invalid data (zero sum or empty)\n\n");
        }
        
        // Cleanup
        free(measured);
        free(true_values);
        free(norm_measured);
        free(norm_true);
    }
    
    closedir(dir);
    
    if (result_count == 0) {
        printf("❌ No valid stats files found\n");
        return -1;
    }
    
    // Sort results by EMD
    qsort(results, result_count, sizeof(TestResult), compare_results);
    
    // Save results to file
    char output_file[MAX_FILENAME];
    snprintf(output_file, sizeof(output_file), "%s/results_emd.txt", folder_path);
    
    FILE* out = fopen(output_file, "w");
    if (!out) {
        fprintf(stderr, "❌ Cannot create output file: %s\n", output_file);
        return -1;
    }
    
    fprintf(out, "# Earth Mover's Distance Results\n");
    fprintf(out, "# Generated: %s %s\n", __DATE__, __TIME__);
    fprintf(out, "# Format: x1 x2 x3 x4 x5 x6 x7 EMD AD_EMD\n");
    fprintf(out, "# Total parameter sets: %d\n", result_count);
    fprintf(out, "# Stats files processed: %d\n", stats_files_processed);
    fprintf(out, "# AD Stats files processed: %d\n", ad_stats_files_processed);
    fprintf(out, "#\n");
    
    // Calculate statistics
    double sum_emd = 0.0;
    double min_emd = INFINITY;
    double max_emd = -INFINITY;
    int valid_count = 0;
    
    double sum_ad_emd = 0.0;
    double min_ad_emd = INFINITY;
    double max_ad_emd = -INFINITY;
    int valid_ad_count = 0;
    
    for (int i = 0; i < result_count; i++) {
        fprintf(out, "%d %d %d %d %d %d %d %.10f %.10f\n",
                results[i].x1, results[i].x2, results[i].x3,
                results[i].x4, results[i].x5, results[i].x6,
                results[i].x7, results[i].emd, results[i].ad_emd);
        
        if (!isnan(results[i].emd)) {
            sum_emd += results[i].emd;
            if (results[i].emd < min_emd) min_emd = results[i].emd;
            if (results[i].emd > max_emd) max_emd = results[i].emd;
            valid_count++;
        }
        
        if (!isnan(results[i].ad_emd)) {
            sum_ad_emd += results[i].ad_emd;
            if (results[i].ad_emd < min_ad_emd) min_ad_emd = results[i].ad_emd;
            if (results[i].ad_emd > max_ad_emd) max_ad_emd = results[i].ad_emd;
            valid_ad_count++;
        }
    }
    
    fclose(out);
    
    // Print summary
    printf("=========================================\n");
    printf("✅ Complete!\n");
    printf("📁 Results saved to: %s\n", output_file);
    printf("\n");
    printf("Summary:\n");
    printf("  Total parameter sets: %d\n", result_count);
    printf("  Stats files processed: %d\n", stats_files_processed);
    printf("  AD Stats files processed: %d\n", ad_stats_files_processed);
    
    if (valid_count > 0) {
        printf("\n  Regular EMD:\n");
        printf("    Valid values: %d\n", valid_count);
        printf("    Min: %.10f\n", min_emd);
        printf("    Max: %.10f\n", max_emd);
        printf("    Mean: %.10f\n", sum_emd / valid_count);
    } else {
        printf("  No valid regular EMD values found\n");
    }
    
    if (valid_ad_count > 0) {
        printf("\n  AD EMD:\n");
        printf("    Valid values: %d\n", valid_ad_count);
        printf("    Min: %.10f\n", min_ad_emd);
        printf("    Max: %.10f\n", max_ad_emd);
        printf("    Mean: %.10f\n", sum_ad_emd / valid_ad_count);
    } else {
        printf("  No valid AD EMD values found\n");
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
