// file: test_chain_1.c
// Combines both test_command_centre and test_eval_scan functionality

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>

#include "common.h"
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "vertical_profiles.h"
#include "radars.h"
#include "processing.h"
#include "control_centre.h"
#include "analysis.h"



// External globals (defined in your code)
extern Raincell* raincell_list[];
extern Spatial_raincell* s_raincell_list[];
extern int raincell_count;
extern Radar* radar_list[];
extern int radar_count;

int main() {
    // Variables to be initialized
    VPR *VPR_strat = NULL;
    VPR *VPR_conv = NULL;
    VPR *VPR_A_clima = NULL;
    VPR *VPR_A_gmd = NULL;
    VPR *VPR_A_d = NULL;
    VPR *VPR_dummy = NULL;
    VPR_params *params = NULL;
    Raincell *raincell = NULL;
    Spatial_raincell *s_raincell = NULL;
    double cart_grid_res = 0.0;
    double sim_time = 0.0;
    
    printf("=== Initializing Test Environment ===\n");
    
    // Initialize everything at once
    initialize_test_environment(
        &VPR_strat, &VPR_conv, &VPR_A_clima, &VPR_A_gmd, &VPR_A_d, &VPR_dummy,
        &params, &raincell, &s_raincell, &cart_grid_res, &sim_time
    );
    
    printf("✓ VPR profiles initialized\n");
    printf("✓ Raincell and spatial raincell created\n");
    printf("✓ Radars created and added to list\n");
    printf("✓ Cart grid resolution: %.0f m\n", cart_grid_res);
    printf("✓ Simulation time: %.1f minutes\n\n", sim_time);
    
    // =========================================
    // Part 1: Run test_command_centre functionality
    // =========================================
    printf("=== Running Command Centre Tests ===\n");
    
    int max_vol_scans = (int)((330.0 - sim_time) / 5);
    for (int i = 0; i < max_vol_scans; i++) {
        generate_commands_file(i, sim_time);
        sim_time += 5.0;
    }
    printf("✓ Generated %d command files\n", max_vol_scans);
    
    // Start monitoring inputs
    monitor_and_process_inputs(VPR_strat, params, VPR_conv);
    
    // =========================================
    // Part 2: Run test_eval_scan functionality
    // =========================================
    printf("\n=== Running Eval Scan Tests ===\n");
    
    #define NUM_SCANS 54
    RainfallStats stats_array[NUM_SCANS];
    init_stats_array(stats_array, NUM_SCANS);
    
    for (int scan_idx = 0; scan_idx < NUM_SCANS; scan_idx++) {
        char filename[256];
        snprintf(filename, sizeof(filename), "outputs/radar_scan_%04d.txt", scan_idx);
        
            read_radar_scans(filename);
    if (scan_count == 0) continue;

    Cart_grid **cart_grids = malloc(scan_count * sizeof(Cart_grid*));
    if (!cart_grids) exit(1);

    int cg_count = 0;

    for (int i = 0; i < scan_count; i++) {
        Polar_box* p_box = radar_scans[i].box;
        Radar* radar = radar_scans[i].radar;
        double time = radar_scans[i].time;
        double time_s_2 = time * 60;

        update_VPR(VPR_strat, params, time_s_2, VPR_conv);

        Cart_grid *cg = interpolate_scan_NN(p_box, radar, time, cart_grid_res, scan_idx, i);
        if (cg) cart_grids[cg_count++] = cg;
    }

    Vol_scan *vol = init_vol_scan(cart_grids, cg_count);
    for (int i = 0; i < cg_count; i++) {
        add_cart_grid_to_volscan(vol, cart_grids[i], i);
    }

    process_volume_scan_VPR(vol);
    compute_average_empVPR(vol);
    compute_std_dev_empVPR(vol);

    double true_time_min = radar_scans[scan_count-1].time +
                           (radar_scans[scan_count-1].time - radar_scans[scan_count-2].time);
    double true_time = true_time_min * 60.0;

    update_VPR(VPR_strat, params, true_time, VPR_conv);

    Point* raincell_pos = get_position_raincell(true_time, s_raincell);
    if (!raincell_pos) exit(EXIT_FAILURE);

    if (fill_refl_ALA_grid(vol, raincell_pos, raincell, VPR_strat, VPR_conv) != 0) {
        exit(EXIT_FAILURE);
    }

    compute_display_grid_KNMI_empirical(vol, -5.0, 0.5, 0);

    double volume_duration = 5.0 * 60.0;
    if (compute_and_store_stats(vol, -5.0, cart_grid_res, volume_duration, stats_array, scan_idx) == 0) {
        append_stats_to_file(stats_array, scan_idx, "outputs/stats.txt");
    }

    for (int i = 0; i < cg_count; i++)
        free_cart_grid(cart_grids[i]);
    free(cart_grids);
    free_vol_scan(vol);

        if (scan_idx % 10 == 0) {
            printf("  Processing scan %d/%d...\n", scan_idx + 1, NUM_SCANS);
        }
    }
    
    // =========================================
    // Cleanup
    // =========================================
    printf("\n=== Cleaning Up ===\n");
    cleanup_test_environment(
        VPR_strat, VPR_conv, VPR_A_clima, VPR_A_gmd, VPR_A_d, VPR_dummy,
        params, raincell, s_raincell
    );
    
    printf("✓ Cleanup complete\n");
    printf("✓ Test environment combined successfully!\n");
    
    return 0;
}
