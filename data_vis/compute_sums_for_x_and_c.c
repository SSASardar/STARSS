#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <dirent.h>
#include <sys/stat.h>
#include <regex.h>

#define MAX_FILENAME 512
#define MAX_LINE 1024
#define MAX_RESULTS 10000

// Band tags
typedef enum {
    BAND_X = 0,
    BAND_C = 1,
    BAND_NONE = -1
} Band;

// Structure to hold parameters from filename.
// NOTE: x4 and x5 are stored ENCODED (as they appear in the filename).
// Decoding happens only at output time:
//     x4_physical = x4 / 100
//     x5_physical = (x5 / 100) - 50
typedef struct {
    int x1;  // radius of convective core (km)
    int x2;  // maximum rainfall intensity (mm/hr)
    int x3;  // apparent motion (m/s)
    int x4;  // cloud base height (km), encoded as value*100 in filename
    int x5;  // sub-cloud gradient (x1e-4), encoded as (value+50)*100 in filename
    int x6;  // minimum distance to C-band radar (km)
    int x7;  // storm duration (minutes)
    double stats_discrepancy;   // True - Measured for this band's stats file
    int stats_scan_count;
    Band band;
} TestResult;

// Extract parameters from a filename matching one of:
//   stats_X_x1_..._x7_....txt
//   stats_C_x1_..._x7_....txt
// Returns 0 on success, -1 on failure.
int extract_parameters(const char* filename, TestResult* result) {
    regex_t regex;
    regmatch_t matches[10];

    // Groups:
    //   1: band letter (X or C)
    //   2..8: x1..x7 (encoded as in the Makefile)
    const char* pattern =
        "^stats_([XC])_x1_([0-9]+)_x2_([0-9]+)_x3_([0-9]+)_x4_([0-9]+)"
        "_x5_([0-9]+)_x6_([0-9]+)_x7_([0-9]+)\\.txt$";

    if (regcomp(&regex, pattern, REG_EXTENDED) != 0) {
        fprintf(stderr, "Failed to compile regex\n");
        return -1;
    }

    if (regexec(&regex, filename, 9, matches, 0) != 0) {
        regfree(&regex);
        return -1;
    }

    if (matches[1].rm_so == -1) {
        regfree(&regex);
        return -1;
    }
    char band_char = filename[matches[1].rm_so];

    int* fields[7] = {
        &result->x1, &result->x2, &result->x3, &result->x4,
        &result->x5, &result->x6, &result->x7
    };

    char buffer[32];
    for (int i = 0; i < 7; i++) {
        regmatch_t* m = &matches[i + 2];
        int len = m->rm_eo - m->rm_so;
        if (len <= 0 || len >= (int)sizeof(buffer)) {
            regfree(&regex);
            return -1;
        }
        snprintf(buffer, len + 1, "%.*s", len, filename + m->rm_so);
        *fields[i] = atoi(buffer);
    }

    regfree(&regex);

    if (band_char == 'X') {
        result->band = BAND_X;
    } else if (band_char == 'C') {
        result->band = BAND_C;
    } else {
        return -1;
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

    if (fgets(line, sizeof(line), file) == NULL) {
        fclose(file);
        return -1;
    }

    while (fgets(line, sizeof(line), file) != NULL) {
        int scan_idx;
        double mse, mae, bias;
        double total_meas_row, total_true_row;
        double total_meas_mm2_row, total_true_mm2_row;

        if (sscanf(line, "%d %lf %lf %lf %lf %lf %lf %lf",
                   &scan_idx, &mse, &mae, &bias,
                   &total_meas_row, &total_true_row,
                   &total_meas_mm2_row, &total_true_mm2_row) == 8) {
            sum_meas += total_meas_mm2_row;
            sum_true += total_true_mm2_row;
            count++;
        }
    }

    fclose(file);

    if (count == 0) {
        return -1;
    }

    *discrepancy = sum_true - sum_meas;
    *scan_count = count;
    return 0;
}

// Sort by x1..x7 (ascending, encoded values — sorting order is same as decoded order
// because decoding is a monotonic affine transform of each coordinate)
int compare_results(const void* a, const void* b) {
    const TestResult* ra = (const TestResult*)a;
    const TestResult* rb = (const TestResult*)b;

    if (ra->x1 != rb->x1) return ra->x1 - rb->x1;
    if (ra->x2 != rb->x2) return ra->x2 - rb->x2;
    if (ra->x3 != rb->x3) return ra->x3 - rb->x3;
    if (ra->x4 != rb->x4) return ra->x4 - rb->x4;
    if (ra->x5 != rb->x5) return ra->x5 - rb->x5;
    if (ra->x6 != rb->x6) return ra->x6 - rb->x6;
    return ra->x7 - rb->x7;
}

// Find or create result entry
TestResult* find_or_create_result(TestResult* results, int* count, const TestResult* new_result) {
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

    if (*count < MAX_RESULTS) {
        results[*count] = *new_result;
        results[*count].stats_discrepancy = NAN;
        results[*count].stats_scan_count = 0;
        (*count)++;
        return &results[*count - 1];
    }

    return NULL;
}

// Write one band's results file (x4 and x5 are DECODED to physical values)
void write_results_file(const char* folder_path, Band band,
                        TestResult* results, int result_count,
                        int files_processed) {
    const char* band_label = (band == BAND_X) ? "X" : "C";
    const char* band_desc  = (band == BAND_X)
        ? "X-band radar"
        : "C-band radar";

    char output_file[MAX_FILENAME];
    snprintf(output_file, sizeof(output_file),
             "%s/results_sums_%s.txt", folder_path, band_label);

    FILE* out = fopen(output_file, "w");
    if (!out) {
        fprintf(stderr, "Cannot create output file: %s\n", output_file);
        return;
    }

    fprintf(out, "# Total Rainfall Accumulation Discrepancy Results (%s)\n", band_desc);
    fprintf(out, "# Generated: %s %s\n", __DATE__, __TIME__);
    fprintf(out, "# Format: x1 x2 x3 x4 x5 x6 x7 Stats_Discrepancy\n");
    fprintf(out, "# Total parameter sets: %d\n", result_count);
    fprintf(out, "# Stats files processed: %d\n", files_processed);
    fprintf(out, "#\n");
    fprintf(out, "# Column descriptions (all physical units):\n");
    fprintf(out, "#   x1 - radius of convective core (km)\n");
    fprintf(out, "#   x2 - maximum rainfall intensity (mm/hr)\n");
    fprintf(out, "#   x3 - apparent motion (m/s)\n");
    fprintf(out, "#   x4 - cloud base height (km)\n");
    fprintf(out, "#   x5 - sub-cloud reflectivity gradient (x1e-4)\n");
    fprintf(out, "#   x6 - minimum distance to C-band radar (km)\n");
    fprintf(out, "#   x7 - storm duration (minutes)\n");
    fprintf(out, "#   Stats_Discrepancy - Sum(True) - Sum(Measured)\n");
    fprintf(out, "#     Positive value means true accumulation > measured accumulation\n");
    fprintf(out, "#     Negative value means measured accumulation > true accumulation\n");
    fprintf(out, "#\n");

    for (int i = 0; i < result_count; i++) {
        // Decode x4 and x5 to physical values
        int x4_physical = results[i].x4 / 100;                  // e.g. 200 -> 2
        int x5_physical = (results[i].x5 / 100) - 50;           // e.g. 4400 -> -6

        fprintf(out, "%d %d %d %d %d %d %d %.10f\n",
                results[i].x1,
                results[i].x2,
                results[i].x3,
                x4_physical,
                x5_physical,
                results[i].x6,
                results[i].x7,
                results[i].stats_discrepancy);
    }

    fclose(out);

    // Compute summary
    double sum_disc = 0.0;
    int valid = 0;
    for (int i = 0; i < result_count; i++) {
        if (!isnan(results[i].stats_discrepancy)) {
            sum_disc += results[i].stats_discrepancy;
            valid++;
        }
    }

    printf("=========================================\n");
    printf("  %s summary\n", band_desc);
    printf("=========================================\n");
    printf("  Results saved to: %s\n", output_file);
    printf("  Total parameter sets: %d\n", result_count);
    printf("  Stats files processed: %d\n", files_processed);
    if (valid > 0) {
        printf("  Valid discrepancy values: %d\n", valid);
        printf("  Mean discrepancy: %.10f\n", sum_disc / valid);
        printf("  Sum discrepancy:  %.10f\n", sum_disc);
    } else {
        printf("  No valid discrepancy values\n");
    }
    printf("\n");
}

int process_batch_folder(const char* folder_path) {
    DIR* dir;
    struct dirent* entry;
    struct stat statbuf;
    char filepath[MAX_FILENAME];

    TestResult results_X[MAX_RESULTS];
    TestResult results_C[MAX_RESULTS];
    int count_X = 0;
    int count_C = 0;
    int files_X = 0;
    int files_C = 0;

    dir = opendir(folder_path);
    if (!dir) {
        fprintf(stderr, "Cannot open directory: %s\n", folder_path);
        return -1;
    }

    printf("=========================================\n");
    printf("  RAINFALL ACCUMULATION DISCREPANCY\n");
    printf("=========================================\n");
    printf("Processing folder: %s\n\n", folder_path);

    while ((entry = readdir(dir)) != NULL) {
        if (strncmp(entry->d_name, "stats_X_x1_", 11) != 0 &&
            strncmp(entry->d_name, "stats_C_x1_", 11) != 0) {
            continue;
        }

        snprintf(filepath, sizeof(filepath), "%s/%s", folder_path, entry->d_name);

        if (stat(filepath, &statbuf) != 0) {
            continue;
        }
        if (!S_ISREG(statbuf.st_mode)) {
            continue;
        }

        TestResult result;
        memset(&result, 0, sizeof(TestResult));
        result.stats_discrepancy = NAN;
        result.band = BAND_NONE;

        if (extract_parameters(entry->d_name, &result) != 0) {
            fprintf(stderr, "  Skipping: %s (cannot parse filename)\n", entry->d_name);
            continue;
        }

        double discrepancy = 0.0;
        int scan_count = 0;
        if (read_stats_file(filepath, &discrepancy, &scan_count) != 0) {
            fprintf(stderr, "  Skipping: %s (cannot read file)\n", entry->d_name);
            continue;
        }

        TestResult* arr = (result.band == BAND_X) ? results_X : results_C;
        int* cnt       = (result.band == BAND_X) ? &count_X     : &count_C;

        TestResult* slot = find_or_create_result(arr, cnt, &result);
        if (slot) {
            slot->stats_discrepancy = discrepancy;
            slot->stats_scan_count  = scan_count;
            slot->band              = result.band;

            if (result.band == BAND_X) {
                files_X++;
            } else {
                files_C++;
            }
        }
    }

    closedir(dir);

    if (count_X == 0 && count_C == 0) {
        printf("No valid stats files found in %s\n", folder_path);
        return -1;
    }

    if (count_X > 0) {
        qsort(results_X, count_X, sizeof(TestResult), compare_results);
        write_results_file(folder_path, BAND_X, results_X, count_X, files_X);
    } else {
        printf("No X-band stats files found.\n");
    }

    if (count_C > 0) {
        qsort(results_C, count_C, sizeof(TestResult), compare_results);
        write_results_file(folder_path, BAND_C, results_C, count_C, files_C);
    } else {
        printf("No C-band stats files found.\n");
    }

    return 0;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <batch_folder>\n", argv[0]);
        fprintf(stderr, "Example: %s batch_test_20260506_155323\n", argv[0]);
        return 1;
    }

    return process_batch_folder(argv[1]);
}
