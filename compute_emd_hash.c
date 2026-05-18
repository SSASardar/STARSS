#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <dirent.h>
#include <sys/stat.h>
#include <regex.h>

#define MAX_FILENAME 512
#define MAX_LINE 1024
#define MAX_HASH_TABLE 200000  // For up to 200k entries

typedef struct {
    int r, m, c, k, y, a;
    double emd_regular;
    double emd_adaptive;
    int has_regular;
    int has_adaptive;
} ResultEntry;

typedef struct HashNode {
    int r, m, c, k, y, a;
    double emd_regular;
    double emd_adaptive;
    int has_regular;
    int has_adaptive;
    struct HashNode* next;
} HashNode;

HashNode* hash_table[MAX_HASH_TABLE];

// Simple hash function for parameter combination
unsigned int hash_params(int r, int m, int c, int k, int y, int a) {
    unsigned int hash = 0;
    hash = hash * 31 + r;
    hash = hash * 31 + m;
    hash = hash * 31 + c;
    hash = hash * 31 + k;
    hash = hash * 31 + y;
    hash = hash * 31 + a;
    return hash % MAX_HASH_TABLE;
}

// Find or create hash node
HashNode* find_or_create(int r, int m, int c, int k, int y, int a) {
    unsigned int idx = hash_params(r, m, c, k, y, a);
    HashNode* node = hash_table[idx];
    
    while (node) {
        if (node->r == r && node->m == m && node->c == c && 
            node->k == k && node->y == y && node->a == a) {
            return node;
        }
        node = node->next;
    }
    
    // Create new node
    node = (HashNode*)malloc(sizeof(HashNode));
    if (!node) return NULL;
    
    node->r = r;
    node->m = m;
    node->c = c;
    node->k = k;
    node->y = y;
    node->a = a;
    node->emd_regular = NAN;
    node->emd_adaptive = NAN;
    node->has_regular = 0;
    node->has_adaptive = 0;
    node->next = hash_table[idx];
    hash_table[idx] = node;
    
    return node;
}

// Extract parameters from filename
int extract_parameters(const char* filename, int* r, int* m, int* c, int* k, int* y, int* a) {
    regex_t regex;
    regmatch_t matches[7];
    
    const char* pattern = "stats_r_([0-9]+)_m_([0-9]+)_c_([0-9]+)_k_([0-9]+)_y_([0-9]+)_a_([0-9]+)\\.txt";
    
    if (regcomp(&regex, pattern, REG_EXTENDED) != 0) {
        return -1;
    }
    
    if (regexec(&regex, filename, 7, matches, 0) == 0) {
        char buffer[32];
        
        int len = matches[1].rm_eo - matches[1].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[1].rm_so);
        *r = atoi(buffer);
        
        len = matches[2].rm_eo - matches[2].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[2].rm_so);
        *m = atoi(buffer);
        
        len = matches[3].rm_eo - matches[3].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[3].rm_so);
        *c = atoi(buffer);
        
        len = matches[4].rm_eo - matches[4].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[4].rm_so);
        *k = atoi(buffer);
        
        len = matches[5].rm_eo - matches[5].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[5].rm_so);
        *y = atoi(buffer);
        
        len = matches[6].rm_eo - matches[6].rm_so;
        snprintf(buffer, len + 1, "%.*s", len, filename + matches[6].rm_so);
        *a = atoi(buffer);
        
        regfree(&regex);
        return 0;
    }
    
    regfree(&regex);
    return -1;
}

// Read stats file and compute EMD
double compute_emd_from_file(const char* filename) {
    FILE* file = fopen(filename, "r");
    if (!file) return NAN;
    
    char line[MAX_LINE];
    double* meas = NULL;
    double* truth = NULL;
    int capacity = 1000;
    int size = 0;
    
    meas = (double*)malloc(capacity * sizeof(double));
    truth = (double*)malloc(capacity * sizeof(double));
    
    if (!meas || !truth) {
        fclose(file);
        free(meas);
        free(truth);
        return NAN;
    }
    
    // Skip header
    if (fgets(line, sizeof(line), file) == NULL) {
        fclose(file);
        free(meas);
        free(truth);
        return NAN;
    }
    
    // Read all data lines
    while (fgets(line, sizeof(line), file) != NULL) {
        int scan_idx;
        double mse, mae, bias, total_meas, total_true, total_meas_mm2, total_true_mm2;
        
        if (sscanf(line, "%d %lf %lf %lf %lf %lf %lf %lf",
                   &scan_idx, &mse, &mae, &bias, 
                   &total_meas, &total_true, 
                   &total_meas_mm2, &total_true_mm2) == 8) {
            
            if (size >= capacity) {
                capacity *= 2;
                meas = (double*)realloc(meas, capacity * sizeof(double));
                truth = (double*)realloc(truth, capacity * sizeof(double));
                if (!meas || !truth) {
                    fclose(file);
                    free(meas);
                    free(truth);
                    return NAN;
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
        return NAN;
    }
    
    // Normalize and compute EMD
    double sum_meas = 0.0, sum_truth = 0.0;
    for (int i = 0; i < size; i++) {
        sum_meas += meas[i];
        sum_truth += truth[i];
    }
    
    if (sum_meas == 0.0 || sum_truth == 0.0) {
        free(meas);
        free(truth);
        return NAN;
    }
    
    // Normalize and compute cumulative difference
    double cum_meas = 0.0, cum_truth = 0.0;
    double emd = 0.0;
    
    for (int i = 0; i < size; i++) {
        cum_meas += meas[i] / sum_meas;
        cum_truth += truth[i] / sum_truth;
        emd += fabs(cum_meas - cum_truth);
    }
    
    emd = emd / size;
    
    free(meas);
    free(truth);
    
    return emd;
}

// Process all files in directory
int process_batch_folder(const char* folder_path) {
    DIR* dir;
    struct dirent* entry;
    char filepath[MAX_FILENAME];
    int regular_count = 0;
    int adaptive_count = 0;
    int error_count = 0;
    
    dir = opendir(folder_path);
    if (!dir) {
        fprintf(stderr, "❌ Cannot open directory: %s\n", folder_path);
        return -1;
    }
    
    printf("=========================================\n");
    printf("  EARTH MOVER'S DISTANCE COMPUTATION\n");
    printf("=========================================\n");
    printf("Processing folder: %s\n\n", folder_path);
    
    // First pass: Process regular stats files
    printf("Pass 1: Processing regular stats files...\n");
    while ((entry = readdir(dir)) != NULL) {
        if (strstr(entry->d_name, "stats_r_") != NULL && 
            strstr(entry->d_name, "ad_stats_r_") == NULL) {
            
            snprintf(filepath, sizeof(filepath), "%s/%s", folder_path, entry->d_name);
            
            int r, m, c, k, y, a;
            if (extract_parameters(entry->d_name, &r, &m, &c, &k, &y, &a) != 0) {
                error_count++;
                continue;
            }
            
            double emd = compute_emd_from_file(filepath);
            if (!isnan(emd)) {
                HashNode* node = find_or_create(r, m, c, k, y, a);
                if (node) {
                    node->emd_regular = emd;
                    node->has_regular = 1;
                    regular_count++;
                }
            } else {
                error_count++;
            }
            
            // Progress indicator
            if ((regular_count + adaptive_count) % 1000 == 0) {
                printf("  Processed %d regular files...\n", regular_count);
            }
        }
    }
    
    printf("  Completed: %d regular files processed\n\n", regular_count);
    
    // Second pass: Process adaptive stats files
    printf("Pass 2: Processing adaptive stats files...\n");
    rewinddir(dir);  // Reset directory position
    
    while ((entry = readdir(dir)) != NULL) {
        if (strstr(entry->d_name, "ad_stats_r_") != NULL) {
            
            snprintf(filepath, sizeof(filepath), "%s/%s", folder_path, entry->d_name);
            
            int r, m, c, k, y, a;
            // Remove "ad_" prefix for parameter extraction
            char* clean_name = strdup(entry->d_name + 3);  // Skip "ad_"
            if (extract_parameters(clean_name, &r, &m, &c, &k, &y, &a) != 0) {
                free(clean_name);
                error_count++;
                continue;
            }
            free(clean_name);
            
            double emd = compute_emd_from_file(filepath);
            if (!isnan(emd)) {
                HashNode* node = find_or_create(r, m, c, k, y, a);
                if (node) {
                    node->emd_adaptive = emd;
                    node->has_adaptive = 1;
                    adaptive_count++;
                }
            } else {
                error_count++;
            }
            
            // Progress indicator
            if ((adaptive_count) % 1000 == 0) {
                printf("  Processed %d adaptive files...\n", adaptive_count);
            }
        }
    }
    
    closedir(dir);
    
    printf("  Completed: %d adaptive files processed\n\n", adaptive_count);
    
    // Write results to file (sorted by parameters)
    char output_file[MAX_FILENAME];
    snprintf(output_file, sizeof(output_file), "%s/emd_results.txt", folder_path);
    
    FILE* out = fopen(output_file, "w");
    if (!out) {
        fprintf(stderr, "❌ Cannot create output file: %s\n", output_file);
        return -1;
    }
    
    fprintf(out, "# Earth Mover's Distance Results\n");
    fprintf(out, "# Generated: %s %s\n", __DATE__, __TIME__);
    fprintf(out, "# Format: r m c k y a regular_EMD adaptive_EMD\n");
    fprintf(out, "# Total regular files: %d\n", regular_count);
    fprintf(out, "# Total adaptive files: %d\n", adaptive_count);
    fprintf(out, "# Total parameter sets: %d\n", regular_count + adaptive_count);
    fprintf(out, "# Errors: %d\n", error_count);
    fprintf(out, "#\n");
    
    // Collect and sort all entries
    ResultEntry* entries = (ResultEntry*)malloc((regular_count + adaptive_count) * sizeof(ResultEntry));
    int entry_count = 0;
    
    for (int i = 0; i < MAX_HASH_TABLE; i++) {
        HashNode* node = hash_table[i];
        while (node) {
            entries[entry_count].r = node->r;
            entries[entry_count].m = node->m;
            entries[entry_count].c = node->c;
            entries[entry_count].k = node->k;
            entries[entry_count].y = node->y;
            entries[entry_count].a = node->a;
            entries[entry_count].emd_regular = node->emd_regular;
            entries[entry_count].emd_adaptive = node->emd_adaptive;
            entries[entry_count].has_regular = node->has_regular;
            entries[entry_count].has_adaptive = node->has_adaptive;
            entry_count++;
            node = node->next;
        }
    }
    
    // Sort entries by parameters for consistent output
    for (int i = 0; i < entry_count - 1; i++) {
        for (int j = i + 1; j < entry_count; j++) {
            if (entries[i].r > entries[j].r ||
                (entries[i].r == entries[j].r && entries[i].m > entries[j].m) ||
                (entries[i].r == entries[j].r && entries[i].m == entries[j].m && entries[i].c > entries[j].c) ||
                (entries[i].r == entries[j].r && entries[i].m == entries[j].m && entries[i].c == entries[j].c && entries[i].k > entries[j].k) ||
                (entries[i].r == entries[j].r && entries[i].m == entries[j].m && entries[i].c == entries[j].c && entries[i].k == entries[j].k && entries[i].y > entries[j].y) ||
                (entries[i].r == entries[j].r && entries[i].m == entries[j].m && entries[i].c == entries[j].c && entries[i].k == entries[j].k && entries[i].y == entries[j].y && entries[i].a > entries[j].a)) {
                ResultEntry temp = entries[i];
                entries[i] = entries[j];
                entries[j] = temp;
            }
        }
    }
    
    // Write results
    int complete_pairs = 0;
    double sum_regular = 0.0, sum_adaptive = 0.0;
    int regular_valid = 0, adaptive_valid = 0;
    
    for (int i = 0; i < entry_count; i++) {
        fprintf(out, "%d %d %d %d %d %d ", 
                entries[i].r, entries[i].m, entries[i].c,
                entries[i].k, entries[i].y, entries[i].a);
        
        if (entries[i].has_regular) {
            fprintf(out, "%.10f ", entries[i].emd_regular);
            sum_regular += entries[i].emd_regular;
            regular_valid++;
        } else {
            fprintf(out, "NA ");
        }
        
        if (entries[i].has_adaptive) {
            fprintf(out, "%.10f\n", entries[i].emd_adaptive);
            sum_adaptive += entries[i].emd_adaptive;
            adaptive_valid++;
            if (entries[i].has_regular) complete_pairs++;
        } else {
            fprintf(out, "NA\n");
        }
    }
    
    fclose(out);
    
    // Free hash table memory
    for (int i = 0; i < MAX_HASH_TABLE; i++) {
        HashNode* node = hash_table[i];
        while (node) {
            HashNode* next = node->next;
            free(node);
            node = next;
        }
    }
    
    free(entries);
    
    // Print summary
    printf("=========================================\n");
    printf("✅ Complete!\n");
    printf("📁 Results saved to: %s\n", output_file);
    printf("\n");
    printf("Summary:\n");
    printf("  Regular files processed: %d\n", regular_count);
    printf("  Adaptive files processed: %d\n", adaptive_count);
    printf("  Complete parameter pairs: %d\n", complete_pairs);
    printf("  Errors: %d\n", error_count);
    printf("\n");
    if (regular_valid > 0) {
        printf("  Regular EMD mean: %.10f\n", sum_regular / regular_valid);
    }
    if (adaptive_valid > 0) {
        printf("  Adaptive EMD mean: %.10f\n", sum_adaptive / adaptive_valid);
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
