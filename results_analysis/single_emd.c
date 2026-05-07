#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_LINE 1024
#define MAX_SCANS 1000

// Compute Earth Mover's Distance (1D Wasserstein distance)
double compute_emd(double* dist1, double* dist2, int count) {
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

// Read stats file and extract measured and true rainfall rates (mm2 columns)
int read_stats_file(const char* filename, double** measured, double** true_values, int* count) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        fprintf(stderr, "Error: Cannot open file %s\n", filename);
        return -1;
    }
    
    char line[MAX_LINE];
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
        fprintf(stderr, "Error: No data found in %s\n", filename);
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
    
    // Handle all zeros case
    if (sum < 1e-10) {
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

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <stats_file>\n", argv[0]);
        fprintf(stderr, "Example: %s outputs/stats.txt\n", argv[0]);
        return 1;
    }
    
    const char* filename = argv[1];
    
    // Read stats file
    double* measured = NULL;
    double* true_values = NULL;
    int scan_count = 0;
    
    if (read_stats_file(filename, &measured, &true_values, &scan_count) != 0) {
        return 1;
    }
    
    // Normalize histograms
    double* norm_measured = NULL;
    double* norm_true = NULL;
    int norm_count_meas = 0;
    int norm_count_true = 0;
    
    normalize_histogram(measured, scan_count, &norm_measured, &norm_count_meas);
    normalize_histogram(true_values, scan_count, &norm_true, &norm_count_true);
    
    double emd = NAN;
    
    if (norm_measured && norm_true && norm_count_meas == norm_count_true && norm_count_meas > 0) {
        emd = compute_emd(norm_measured, norm_true, norm_count_meas);
        printf("%.10f\n", emd);
    } else {
        // Check if all zeros
        int all_zero_meas = 1;
        int all_zero_true = 1;
        
        for (int i = 0; i < scan_count; i++) {
            if (measured[i] > 1e-10) all_zero_meas = 0;
            if (true_values[i] > 1e-10) all_zero_true = 0;
        }
        
        if (all_zero_meas && all_zero_true) {
            // Both zero - perfect match
            printf("0.0000000000\n");
        } else if (all_zero_meas || all_zero_true) {
            // One zero, one non-zero - maximum distance
            printf("1.0000000000\n");
        } else {
            fprintf(stderr, "Error: Cannot compute EMD\n");
            free(measured);
            free(true_values);
            return 1;
        }
    }
    
    // Cleanup
    free(measured);
    free(true_values);
    free(norm_measured);
    free(norm_true);
    
    return 0;
}
