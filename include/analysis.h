#ifndef ANALYSIS_H
#define ANALYSIS_H

#include <stdbool.h>
#include <string.h>
//#include "processing.h"  // For Vol_scan and other structures


// Forward declarations instead of full includes
typedef struct Vol_scan Vol_scan;
typedef struct VPR VPR;
typedef struct VPR_params VPR_params;
typedef struct Raincell Raincell;
typedef struct Spatial_raincell Spatial_raincell;
typedef struct Radar Radar;


// Statistics structure definition
typedef struct {
    double mse;
    double mae;
    double bias;
    double total_measured;        // sum of R over grid points
    double total_true;            // sum of R over grid points
    double total_measured_mm2;    // area-corrected total in mm*h per km²
    double total_true_mm2;        // area-corrected total in mm*h per km²
} RainfallStats;






void initialize_test_environment(
    VPR **VPR_strat,
    VPR **VPR_conv,
    VPR **VPR_A_clima,
    VPR **VPR_A_gmd,
    VPR **VPR_A_d,
    VPR **VPR_dummy,
    VPR_params **params,
    Raincell **raincell,
    Spatial_raincell **s_raincell,
    double *cart_grid_res,
    double *sim_time
);


void cleanup_test_environment(
    VPR *VPR_strat,
    VPR *VPR_conv,
    VPR *VPR_A_clima,
    VPR *VPR_A_gmd,
    VPR *VPR_A_d,
    VPR *VPR_dummy,
    VPR_params *params,
    Raincell *raincell,
    Spatial_raincell *s_raincell
);






// Function prototypes for statistics
void init_stats_array(RainfallStats *stats_array, int num_scans);

int compute_and_store_stats(Vol_scan *vol, double rain_threshold, double cart_grid_res, 
                           double volume_duration_seconds, RainfallStats *stats, int scan_idx);
void append_stats_to_file(const RainfallStats *stats_array, int scan_idx, const char *filename);
void print_stats_summary(const RainfallStats *stats_array, int num_scans);
void print_scan_stats_console(const RainfallStats *stats, int scan_idx);

// Function prototypes for additional analysis (you can add more here)
double compute_mean_error(const RainfallStats *stats_array, int num_scans, const char *metric);
double compute_rmse_from_stats(const RainfallStats *stats_array, int num_scans);
void print_error_distribution(const RainfallStats *stats_array, int num_scans);

#endif // ANALYSIS_H
