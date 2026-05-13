#include "analysis.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include <stdbool.h>
#include <time.h>




#include "processing.h"
#include "vertical_profiles.h"  
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "radars.h"







/**
 * Initializes all components needed for testing:
 * - VPR profiles (stratiform, convective, climatology, etc.)
 * - Raincells (normal and spatial components)
 * - Radars and radar list
 * - Returns initialized components for test functions
 */
/*void initialize_test_environment(
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
) {
    // Initialize simulation time
    *sim_time = 60.0;
    
    // Initialize cartesian grid resolution (in meters)
    *cart_grid_res = 1000.0;  // 1 km resolution
    
    // Initialize VPR parameters
    *params = malloc(sizeof(VPR_params));
    init_VPR_params(*params);
    
    fill_VPR_params(*params,
        60.0*60, 120.0*60.0, 170.0*60.0, 200.0*60.0, 230.0*60.0,
        7.0,
        2000.0, 3000.0,
        45.0, 1.0, 1.0, 2.0,
        3000.0, 100.0, 50.0,
        15.0, 2.0, 1.0,
        750.0, 500.0, 250.0,
        0.65, -0.4, -0.15, -0.1,
        35, -3.0, 2.0, 14.0,
        500.0, 150.0, 25.0,
        0.0005
    );
    
    // Create VPR profiles
    *VPR_strat = create_and_fill_VPR(*params);
    *VPR_conv = create_VPR();
    *VPR_dummy = create_VPR();
    *VPR_A_clima = create_VPR();
    *VPR_A_gmd = create_VPR();
    *VPR_A_d = create_VPR();
    
    // Compute VPR profiles
    double t1 = (*params)->t_growth_start;
    double t2 = (*params)->t_decay_end;
    double t3 = (*params)->t_mature_end;
    
    compute_climatology_VPR(*VPR_A_clima, *params, 60.0, 70.0 * 60.0, *VPR_dummy);
    compute_average_VPR(*VPR_A_gmd, *params, t1, t2, 60.0, *VPR_dummy);
    compute_average_VPR(*VPR_A_d, *params, t3, t2, 60.0, *VPR_dummy);
    
    // Initialize raincell and spatial_raincell
    *raincell = create_raincell(1, 0.5, 15000.0, -0.5);
    *s_raincell = create_spatial_raincell(1, -80000.0, 80000.0, 10);
    
    // Add to global lists (if your test functions expect them)
    raincell_list[raincell_count] = *raincell;
    s_raincell_list[raincell_count] = *s_raincell;
    raincell_count++;
    
    // Initialize radars
    Radar* radar1 = create_radar(1, "C", "PPI", 0.0, 0.0, 100.0, 250000.0, 250.0, 1.0);
    Radar* radar2 = create_radar(2, "X", "RHI", -50000.0, 50000.0, 25.0, 50000.0, 100.0, 0.5);
    
    radar_list[radar_count++] = radar1;
    radar_list[radar_count++] = radar2;
}*/
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
   double *sim_time,
    double x1, double x2, double x3, double x4, double x5, double x6
) {
    // Initialize simulation time
    *sim_time = 60.0;
    
    // Initialize cartesian grid resolution (in meters)
    *cart_grid_res = x1;  // Now using x1 from command line
    
    // Calculate dependent variables
    double e1 = (x2 * 60.0 + 230.0 * 60.0) / 2.0;  // Average of x2*60 and 230*60
    double e2 = x3 + 3000.0;  // Bright band height = cloud base + 3000
    
    // Initialize VPR parameters
    *params = malloc(sizeof(VPR_params));
    init_VPR_params(*params);
    
    fill_VPR_params(*params,
        60.0*60, 120.0*60.0, x2*60.0, e1, 230.0*60.0,
        7.0,
        2000.0, 3000.0,
        45.0, 1.0, 1.0, 2.0,
        e2, 100.0, 50.0,
        15.0, 2.0, 1.0,
        750.0, 500.0, 250.0,
        0.65, -0.4, -0.15, -0.1,
        35, -3.0, 2.0, 14.0,
        x3, 150.0, 25.0,
        0.0005
    );
    
    // Create VPR profiles
    *VPR_strat = create_and_fill_VPR(*params);
    *VPR_conv = create_VPR();
    *VPR_dummy = create_VPR();
    *VPR_A_clima = create_VPR();
    *VPR_A_gmd = create_VPR();
    *VPR_A_d = create_VPR();
    
    // Compute VPR profiles
    double t1 = (*params)->t_growth_start;
    double t2 = (*params)->t_decay_end;
    double t3 = (*params)->t_mature_end;
    
    compute_climatology_VPR(*VPR_A_clima, *params, 60.0, 70.0 * 60.0, *VPR_dummy);
    compute_average_VPR(*VPR_A_gmd, *params, t1, t2, 60.0, *VPR_dummy);
    compute_average_VPR(*VPR_A_d, *params, t3, t2, 60.0, *VPR_dummy);
    
    // Initialize raincell and spatial_raincell with command line parameters
    *raincell = create_raincell(1, x4, 15000.0, -0.5);  // x4 is the core ratio
    *s_raincell = create_spatial_raincell(1, -80000.0, x5, x6);  // x5 y-distance, x6 apparent motion
    
    // Add to global lists (if your test functions expect them)
    raincell_list[raincell_count] = *raincell;
    s_raincell_list[raincell_count] = *s_raincell;
    raincell_count++;
    
    // Initialize radars
    Radar* radar0 = create_radar(0, "C", "PPI", 0.0, 0.0, 100.0, 250000.0, 250.0, 1.0);
    Radar* radar1 = create_radar(1, "C", "PPI", 0.0, 0.0, 100.0, 250000.0, 250.0, 1.0);
    Radar* radar2 = create_radar(2, "X", "PPI", -50000.0, 50000.0, 25.0, 50000.0, 100.0, 1.0);
    Radar* radar3 = create_radar(3, "X", "RHI", -50000.0, 50000.0, 25.0, 50000.0, 250.0, 1.0);
    
    radar_list[radar_count++] = radar0;
    radar_list[radar_count++] = radar1;
    radar_list[radar_count++] = radar2;
    radar_list[radar_count++] = radar3;
    
    // Print the calculated dependent variables for verification
//    printf("\n=== Calculated Dependent Variables ===\n");
 //   printf("€1 (mid-decay time):     %.2f seconds (%.2f minutes)\n", e1, e1/60.0);
//    printf("€2 (bright band height): %.2f m\n", e2);
//    printf("=====================================\n\n");
}




/**
 * Cleans up all allocated memory
 */
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
) {
    // Free VPR structures
    free(VPR_strat);
    free(VPR_conv);
    free(VPR_A_clima);
    free(VPR_A_gmd);
    free(VPR_A_d);
    free(VPR_dummy);
    free(params);
    
    // Free raincell structures
    free(raincell);
    free(s_raincell);
    
    // Note: radars and global lists cleanup depends on your application
    // You may want to add radar cleanup here if needed
}







// Initialize all stats to NAN
void init_stats_array(RainfallStats *stats_array, int num_scans) {
    if (!stats_array) return;
    
    for (int i = 0; i < num_scans; i++) {
        stats_array[i].mse = NAN;
        stats_array[i].mae = NAN;
        stats_array[i].bias = NAN;
        stats_array[i].total_measured = NAN;
        stats_array[i].total_true = NAN;
        stats_array[i].total_measured_mm2 = NAN;
        stats_array[i].total_true_mm2 = NAN;
    }
}
int compute_and_store_stats_temp_interp(Vol_scan *vol, double rain_threshold, double cart_grid_res,
                           double volume_duration_seconds, RainfallStats *stats, int scan_idx, int temp_interp_timesteps) {
    if (!vol || !stats || scan_idx < 0) return -1;
    
    double mse, mae, bias;
    double total_measured, total_true_masked;
    double total_measured_mm2, total_true_mm2;
    double total_true_unmasked, total_true_mm2_unmasked;
    
    // Compute rainfall statistics
    if (compute_rainfall_statistics(vol, rain_threshold, cart_grid_res,
                                    &mse, &mae, &bias,
                                    &total_measured, &total_true_masked,
                                    &total_measured_mm2, &total_true_mm2,
                                    &total_true_unmasked, &total_true_mm2_unmasked) == 0) {
        // Store computed statistics
        stats[scan_idx].mse = mse;
        stats[scan_idx].mae = mae;
        stats[scan_idx].bias = bias;
        stats[scan_idx].total_measured = total_measured;
        stats[scan_idx].total_true = total_true_unmasked;
        
        // do not Divide by the actual volume duration
       //stats[scan_idx].total_measured_mm2 = total_measured_mm2;
        //stats[scan_idx].total_true_mm2 = total_true_mm2_unmasked;
        
	// Divide multiply by the time to get to the accumulation in the timeperiod.
        stats[scan_idx].total_measured_mm2 = total_measured_mm2* (volume_duration_seconds/3600);
        stats[scan_idx].total_true_mm2 = total_true_mm2_unmasked*( volume_duration_seconds/3600);
        
        return 0;
    } else {
        return -1;
    }
}



int compute_and_store_stats(Vol_scan *vol, double rain_threshold, double cart_grid_res,
                           double volume_duration_seconds, RainfallStats *stats, int scan_idx) {
    if (!vol || !stats || scan_idx < 0) return -1;
    
    double mse, mae, bias;
    double total_measured, total_true_masked;
    double total_measured_mm2, total_true_mm2;
    double total_true_unmasked, total_true_mm2_unmasked;
    
    // Compute rainfall statistics
    if (compute_rainfall_statistics(vol, rain_threshold, cart_grid_res,
                                    &mse, &mae, &bias,
                                    &total_measured, &total_true_masked,
                                    &total_measured_mm2, &total_true_mm2,
                                    &total_true_unmasked, &total_true_mm2_unmasked) == 0) {
        // Store computed statistics
        stats[scan_idx].mse = mse;
        stats[scan_idx].mae = mae;
        stats[scan_idx].bias = bias;
        stats[scan_idx].total_measured = total_measured;
        stats[scan_idx].total_true = total_true_unmasked;
        
        // do not Divide by the actual volume duration
       //stats[scan_idx].total_measured_mm2 = total_measured_mm2;
        //stats[scan_idx].total_true_mm2 = total_true_mm2_unmasked;
        
	// Divide multiply by the time to get to the accumulation in the timeperiod.
        stats[scan_idx].total_measured_mm2 = total_measured_mm2* (volume_duration_seconds/3600);
        stats[scan_idx].total_true_mm2 = total_true_mm2_unmasked*( volume_duration_seconds/3600);
        
        return 0;
    } else {
        return -1;
    }
}

// Append a single scan's statistics to file (preserving exact original format)
void append_stats_to_file(const RainfallStats *stats_array, int scan_idx, const char *filename) {
    if (!stats_array || !filename || scan_idx < 0) return;
    
    FILE *fp = fopen(filename, "a");  // Open in append mode
    if (!fp) {
        fprintf(stderr, "Failed to open file %s for writing\n", filename);
        return;
    }
    
    // Write header only for first scan (scan_idx == 0)
    if (scan_idx == 0) {
        fprintf(fp, "Scan MSE MAE Bias Total_meas Total_true_unmasked Total_meas_mm2 Total_true_mm2_unmasked\n");
    }
    
    // Write data in EXACT original format
    fprintf(fp, "%d %.5f %.5f %.5f %.5f %.5f %.5f %.5f\n",
            scan_idx,
            stats_array[scan_idx].mse, 
            stats_array[scan_idx].mae, 
            stats_array[scan_idx].bias,
            stats_array[scan_idx].total_measured, 
            stats_array[scan_idx].total_true,
            stats_array[scan_idx].total_measured_mm2, 
            stats_array[scan_idx].total_true_mm2);
    
    fclose(fp);
}

// Print summary statistics to console
void print_stats_summary(const RainfallStats *stats_array, int num_scans) {
    if (!stats_array || num_scans <= 0) return;
    
    int valid_count = 0;
    double sum_mse = 0, sum_mae = 0, sum_bias = 0;
    double sum_meas = 0, sum_true = 0;
    double sum_meas_mm2 = 0, sum_true_mm2 = 0;
    double min_mse = INFINITY, max_mse = -INFINITY;
    double min_mae = INFINITY, max_mae = -INFINITY;
    
    // Calculate statistics
    for (int i = 0; i < num_scans; i++) {
        if (!isnan(stats_array[i].mse)) {
            valid_count++;
            sum_mse += stats_array[i].mse;
            sum_mae += stats_array[i].mae;
            sum_bias += stats_array[i].bias;
            sum_meas += stats_array[i].total_measured;
            sum_true += stats_array[i].total_true;
            sum_meas_mm2 += stats_array[i].total_measured_mm2;
            sum_true_mm2 += stats_array[i].total_true_mm2;
            
            if (stats_array[i].mse < min_mse) min_mse = stats_array[i].mse;
            if (stats_array[i].mse > max_mse) max_mse = stats_array[i].mse;
            if (stats_array[i].mae < min_mae) min_mae = stats_array[i].mae;
            if (stats_array[i].mae > max_mae) max_mae = stats_array[i].mae;
        }
    }
    
    if (valid_count == 0) {
        printf("No valid statistics to summarize\n");
        return;
    }
    
    double mean_mse = sum_mse / valid_count;
    double mean_mae = sum_mae / valid_count;
    double mean_bias = sum_bias / valid_count;
    double mean_meas = sum_meas / valid_count;
    double mean_true = sum_true / valid_count;
    double mean_meas_mm2 = sum_meas_mm2 / valid_count;
    double mean_true_mm2 = sum_true_mm2 / valid_count;
    
    // Calculate standard deviation
    double sq_sum_mse = 0, sq_sum_mae = 0;
    for (int i = 0; i < num_scans; i++) {
        if (!isnan(stats_array[i].mse)) {
            sq_sum_mse += (stats_array[i].mse - mean_mse) * (stats_array[i].mse - mean_mse);
            sq_sum_mae += (stats_array[i].mae - mean_mae) * (stats_array[i].mae - mean_mae);
        }
    }
    double std_mse = sqrt(sq_sum_mse / valid_count);
    double std_mae = sqrt(sq_sum_mae / valid_count);
    
    printf("\n========== STATISTICS SUMMARY ==========\n");
    printf("Valid scans: %d / %d\n", valid_count, num_scans);
    printf("----------------------------------------\n");
    printf("MSE:    mean=%.5f  std=%.5f  min=%.5f  max=%.5f\n", mean_mse, std_mse, min_mse, max_mse);
    printf("MAE:    mean=%.5f  std=%.5f  min=%.5f  max=%.5f\n", mean_mae, std_mae, min_mae, max_mae);
    printf("Bias:   mean=%.5f\n", mean_bias);
    printf("----------------------------------------\n");
    printf("Rainfall (mm/h):\n");
    printf("  Measured: mean=%.5f\n", mean_meas);
    printf("  True:     mean=%.5f\n", mean_true);
    printf("  Bias:     mean=%.5f\n", mean_meas - mean_true);
    printf("----------------------------------------\n");
    printf("Rainfall (mm/h/km²):\n");
    printf("  Measured: mean=%.5f\n", mean_meas_mm2);
    printf("  True:     mean=%.5f\n", mean_true_mm2);
    printf("  Bias:     mean=%.5f\n", mean_meas_mm2 - mean_true_mm2);
    printf("========================================\n");
}

// Print individual scan stats to console (formatted nicely)
void print_scan_stats_console(const RainfallStats *stats, int scan_idx) {
    if (!stats) return;
    
    printf("Scan %3d: MSE=%8.5f MAE=%8.5f Bias=%8.5f "
           "Meas=%8.5f True=%8.5f Meas_mm2=%10.5f True_mm2=%10.5f\n",
           scan_idx,
           stats[scan_idx].mse, 
           stats[scan_idx].mae, 
           stats[scan_idx].bias,
           stats[scan_idx].total_measured, 
           stats[scan_idx].total_true,
           stats[scan_idx].total_measured_mm2, 
           stats[scan_idx].total_true_mm2);
}

// Additional analysis functions
double compute_mean_error(const RainfallStats *stats_array, int num_scans, const char *metric) {
    if (!stats_array || num_scans <= 0) return NAN;
    
    double sum = 0;
    int count = 0;
    
    for (int i = 0; i < num_scans; i++) {
        double value = NAN;
        
        if (strcmp(metric, "mse") == 0) value = stats_array[i].mse;
        else if (strcmp(metric, "mae") == 0) value = stats_array[i].mae;
        else if (strcmp(metric, "bias") == 0) value = stats_array[i].bias;
        else if (strcmp(metric, "measured") == 0) value = stats_array[i].total_measured;
        else if (strcmp(metric, "true") == 0) value = stats_array[i].total_true;
        else return NAN;
        
        if (!isnan(value)) {
            sum += value;
            count++;
        }
    }
    
    return (count > 0) ? sum / count : NAN;
}

double compute_rmse_from_stats(const RainfallStats *stats_array, int num_scans) {
    if (!stats_array || num_scans <= 0) return NAN;
    
    double sum_sq = 0;
    int count = 0;
    
    for (int i = 0; i < num_scans; i++) {
        if (!isnan(stats_array[i].mse)) {
            sum_sq += stats_array[i].mse;
            count++;
        }
    }
    
    return (count > 0) ? sqrt(sum_sq / count) : NAN;
}

void print_error_distribution(const RainfallStats *stats_array, int num_scans) {
    if (!stats_array || num_scans <= 0) return;
    
    int bins_mse[10] = {0};  // 10 bins for MSE distribution
    int bins_mae[10] = {0};  // 10 bins for MAE distribution
    
    double mse_max = 0, mae_max = 0;
    
    // Find max values for binning
    for (int i = 0; i < num_scans; i++) {
        if (!isnan(stats_array[i].mse)) {
            if (stats_array[i].mse > mse_max) mse_max = stats_array[i].mse;
            if (stats_array[i].mae > mae_max) mae_max = stats_array[i].mae;
        }
    }
    
    // Bin the values
    for (int i = 0; i < num_scans; i++) {
        if (!isnan(stats_array[i].mse)) {
            int bin_mse = (int)((stats_array[i].mse / mse_max) * 9);
            int bin_mae = (int)((stats_array[i].mae / mae_max) * 9);
            if (bin_mse >= 0 && bin_mse < 10) bins_mse[bin_mse]++;
            if (bin_mae >= 0 && bin_mae < 10) bins_mae[bin_mae]++;
        }
    }
    
    printf("\n========== ERROR DISTRIBUTION ==========\n");
    printf("MSE distribution (max=%.5f):\n", mse_max);
    for (int i = 0; i < 10; i++) {
        printf("  Bin %d: %d scans\n", i, bins_mse[i]);
    }
    printf("MAE distribution (max=%.5f):\n", mae_max);
    for (int i = 0; i < 10; i++) {
        printf("  Bin %d: %d scans\n", i, bins_mae[i]);
    }
    printf("========================================\n");
}
