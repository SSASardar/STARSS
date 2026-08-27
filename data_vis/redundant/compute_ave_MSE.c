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
    int x5;  // cloud base height (km) - multiplied by 100
    int x6;  // distance to C-band radar (km)
    int x7;  // storm duration (minutes)
    double avg_mse;  // average Mean Squared Error
} TestResult;

// Extract parameters from filename
int extract_parameters(const char* filename, TestResult* result) {
    regex_t regex;
    regmatch_t matches[8];
    
    // Pattern: stats_x1_(\d+)_x2_(\d+)_x3_(\d+)_x4_(\d+)_x5_(\d+)_x6_(\d+)_x7_(\d+)\.txt
    const char* pattern = "stats_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt";
    
    if (regcomp(&regex, pattern, REG_EXTENDED) != 0) {
        fprintf(stderr, "Failed to compile regex\n");
        return -1;
    }
    
    if (regexec(&regex, filename, 8, matches, 0) == 0) {
        char buffer[32];
        
        // Extract each parameter
        int len = matches[1].rm_eo - matches[1].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[1].rm_so);
        result->x1 = atoi(buffer);
        
        len = matches[2].rm_eo - matches[2].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[2].rm_so);
        result->x2 = atoi(buffer);
        
        len = matches[3].rm_eo - matches[3].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[3].rm_so);
        result->x3 = atoi(buffer);
        
        len = matches[4].rm_eo - matches[4].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[4].rm_so);
        result->x4 = atoi(buffer);
        
        len = matches[5].rm_eo - matches[5].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[5].rm_so);
        result->x5 = atoi(buffer);
        
        len = matches[6].rm_eo - matches[6].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[6].rm_so);
        result->x6 = atoi(buffer);
        
        len = matches[7].rm_eo - matches[7].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[7].rm_so);
        result->x7 = atoi(buffer);
        
        regfree(&regex);
        return 0;
    }
    
    regfree(&regex);
    return -1;
}

// Read stats file and compute average MSE
// MSE is the second column in the stats file
int read_stats_file(const char* filename, double* avg_mse, int* scan_count) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        return -1;
    }
    
    char line[MAX_LINE];
    double sum_mse = 0.0;
    int count = 0;
    
    // Skip header
    if (fgets(line, sizeof(line), file) == NULL) {
        fclose(file);
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
            
            sum_mse += mse;
            count++;
        }
    }
    
    fclose(file);
    
    if (count == 0) {
        return -1;
    }
    
    *avg_mse = sum_mse / count;
    *scan_count = count;
    
    return 0;
}

// Main function to process all stats files in a directory
int process_batch_folder(const char* folder_path) {
    DIR* dir;
    struct dirent* entry;
    struct stat statbuf;
    char filepath[MAX_FILENAME];
    TestResult results[MAX_RESULTS];
    int result_count = 0;
    
    // Open directory
    dir = opendir(folder_path);
    if (!dir) {
        fprintf(stderr, "❌ Cannot open directory: %s\n", folder_path);
        return -1;
    }
    
    printf("=========================================\n");
    printf("  AVERAGE MSE COMPUTATION\n");
    printf("=========================================\n");
    printf("Processing folder: %s\n\n", folder_path);
    
    // Process each file
    while ((entry = readdir(dir)) != NULL) {
        // Only process files that start with "stats_x1_" (not "ad_stats_x1_")
        if (strstr(entry->d_name, "stats_x1_") != entry->d_name) {
            continue;
        }
        
        snprintf(filepath, sizeof(filepath), "%s/%s", folder_path, entry->d_name);
        
        // Get file stats
        if (stat(filepath, &statbuf) != 0) {
            continue;
        }
        
        // Extract parameters from filename
        TestResult result;
        if (extract_parameters(entry->d_name, &result) != 0) {
            fprintf(stderr, "  ⚠️ Skipping: %s (cannot parse filename)\n", entry->d_name);
            continue;
        }
        
        // Read stats file and compute average MSE
        int scan_count = 0;
        if (read_stats_file(filepath, &result.avg_mse, &scan_count) != 0) {
            fprintf(stderr, "  ⚠️ Skipping: %s (cannot read file)\n", entry->d_name);
            continue;
        }
        
        // Display result
        printf("[%d] %s\n", result_count + 1, entry->d_name);
        printf("    Parameters: x1=%d x2=%d x3=%d x4=%d x5=%d x6=%d x7=%d\n", 
               result.x1, result.x2, result.x3, result.x4, result.x5, result.x6, result.x7);
        printf("    Scans: %d\n", scan_count);
        printf("    Average MSE: %.10f\n\n", result.avg_mse);
        
        // Store result
        if (result_count < MAX_RESULTS) {
            results[result_count++] = result;
        }
    }
    
    closedir(dir);
    
    if (result_count == 0) {
        printf("❌ No valid stats files found\n");
        return -1;
    }
    
    // Save results to file (in the order they were read)
    char output_file[MAX_FILENAME];
    snprintf(output_file, sizeof(output_file), "%s/avg_mse_results.txt", folder_path);
    
    FILE* out = fopen(output_file, "w");
    if (!out) {
        fprintf(stderr, "❌ Cannot create output file: %s\n", output_file);
        return -1;
    }
    
    fprintf(out, "# Average Mean Squared Error Results\n");
    fprintf(out, "# Generated: %s %s\n", __DATE__, __TIME__);
    fprintf(out, "# Format: x1 x2 x3 x4 x5 x6 x7 Avg_MSE\n");
    fprintf(out, "# Total files processed: %d\n", result_count);
    fprintf(out, "#\n");
    
    // Calculate statistics
    double sum_mse = 0.0;
    double min_mse = INFINITY;
    double max_mse = -INFINITY;
    
    for (int i = 0; i < result_count; i++) {
        fprintf(out, "%d %d %d %d %d %d %d %.10f\n",
                results[i].x1, results[i].x2, results[i].x3,
                results[i].x4, results[i].x5, results[i].x6,
                results[i].x7, results[i].avg_mse);
        
        sum_mse += results[i].avg_mse;
        if (results[i].avg_mse < min_mse) min_mse = results[i].avg_mse;
        if (results[i].avg_mse > max_mse) max_mse = results[i].avg_mse;
    }
    
    fclose(out);
    
    // Print summary
    printf("=========================================\n");
    printf("✅ Complete!\n");
    printf("📁 Results saved to: %s\n", output_file);
    printf("\n");
    printf("Summary:\n");
    printf("  Total files processed: %d\n", result_count);
    printf("  Min Average MSE: %.10f\n", min_mse);
    printf("  Max Average MSE: %.10f\n", max_mse);
    printf("  Mean Average MSE: %.10f\n", sum_mse / result_count);
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
