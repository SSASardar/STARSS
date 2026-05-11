// Combines both test_command_centre and test_eval_scan functionality

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <getopt.h>

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

// Structure to hold command line parameters
typedef struct {
    double x1;  // cartesian grid resolution (m)
    double x2;  // mature phase end time (minutes)
    double x3;  // cloud base height (m)
    double x4;  // core circle ratio
    double x5;  // raincell closest distance in y direction (m)
    double x6;  // apparent motion (units?)
} CommandLineParams;

void print_usage(const char* program_name) {
    printf("Usage: %s [options]\n", program_name);
    printf("Options:\n");
    printf("  -r, --resolution <value>    Cartesian grid resolution in meters (x1, default: 1000.0)\n");
    printf("  -m, --mature-end <value>    Mature phase end time in minutes (x2, default: 170.0)\n");
    printf("  -c, --cloud-base <value>    Cloud base height in meters (x3, default: 500.0)\n");
    printf("  -k, --core-ratio <value>    Core circle ratio (x4, default: 0.5)\n");
    printf("  -y, --y-distance <value>    Raincell closest distance in y direction in meters (x5, default: 80000.0)\n");
    printf("  -a, --apparent-motion <value> Apparent motion (x6, default: 10.0)\n");
    printf("  -h, --help                  Show this help message\n");
    printf("\nExample:\n");
    printf("  %s -r 500 -m 180 -c 600 -k 0.7 -y 75000 -a 12\n", program_name);
}

CommandLineParams parse_command_line(int argc, char *argv[]) {
    CommandLineParams params = {
        .x1 = 1000.0,      // default: 1 km resolution
        .x2 = 170.0,       // default: 170 minutes
        .x3 = 500.0,       // default: 500 m cloud base
        .x4 = 0.5,         // default: 0.5 ratio
        .x5 = 80000.0,     // default: 80 km
        .x6 = 10.0         // default: 10 (units?)
    };
    
    static struct option long_options[] = {
        {"resolution",      required_argument, 0, 'r'},
        {"mature-end",      required_argument, 0, 'm'},
        {"cloud-base",      required_argument, 0, 'c'},
        {"core-ratio",      required_argument, 0, 'k'},
        {"y-distance",      required_argument, 0, 'y'},
        {"apparent-motion", required_argument, 0, 'a'},
        {"help",            no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };
    
    int opt;
    int option_index = 0;
    
    while ((opt = getopt_long(argc, argv, "r:m:c:k:y:a:h", long_options, &option_index)) != -1) {
        switch (opt) {
            case 'r':
                params.x1 = atof(optarg);
                if (params.x1 <= 0) {
                    fprintf(stderr, "Error: Resolution must be positive\n");
                    exit(EXIT_FAILURE);
                }
                break;
            case 'm':
                params.x2 = atof(optarg);
                if (params.x2 <= 0) {
                    fprintf(stderr, "Error: Mature end time must be positive\n");
                    exit(EXIT_FAILURE);
                }
                break;
            case 'c':
                params.x3 = atof(optarg);
                if (params.x3 < 0) {
                    fprintf(stderr, "Error: Cloud base height cannot be negative\n");
                    exit(EXIT_FAILURE);
                }
                break;
            case 'k':
                params.x4 = atof(optarg);
                if (params.x4 < 0 || params.x4 > 1) {
                    fprintf(stderr, "Error: Core ratio must be between 0 and 1\n");
                    exit(EXIT_FAILURE);
                }
                break;
            case 'y':
                params.x5 = atof(optarg);
                break;
            case 'a':
                params.x6 = atof(optarg);
                break;
            case 'h':
                print_usage(argv[0]);
                exit(EXIT_SUCCESS);
            default:
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
        }
    }
    
 /*   // Print the parameters being used
    printf("\n=== Command Line Parameters ===\n");
    printf("x1 (grid resolution):       %.2f m\n", params.x1);
    printf("x2 (mature phase end):      %.2f minutes\n", params.x2);
    printf("x3 (cloud base height):     %.2f m\n", params.x3);
    printf("x4 (core circle ratio):     %.2f\n", params.x4);
    printf("x5 (y-direction distance):  %.2f m\n", params.x5);
    printf("x6 (apparent motion):       %.2f\n", params.x6);
    printf("===============================\n\n");
*/    
    return params;
}
int write_heights_for_point(Vol_scan *vol, int xi, int yi, const char *filename) {
    if (!vol || !vol->grid_height || !vol->grid_refl) return -1;

    FILE *fp = fopen(filename, "w");
    if (!fp) return -1;

//    size_t idx = xi * vol->num_y + yi;

    fprintf(fp, "# Heights for point (%d, %d) across %d PPIs\n", xi, yi, vol->num_PPIs);
    fprintf(fp, "# Format: PPI_index Reflectivity Height\n");

    for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
        //size_t grid_idx = idx + ppi * vol->num_elements;
        size_t grid_idx = ppi * vol->num_x * vol->num_y + xi * vol->num_y + yi;
	    double refl = vol->grid_refl[grid_idx];

            double height = vol->grid_height[grid_idx];
            //fprintf(fp, "%d %.2f\n", ppi, height);
            fprintf(fp, "%d %.2f %.2f\n", ppi, refl, height);
    }

    fclose(fp);
    return 0;
}


int write_VPR_to_file(const VPR *vpr, const char *label, int scan_idx) {
    if (!vpr || !label) return -1;

    char filename[256];
    snprintf(filename, sizeof(filename), "outputs/VPR_%s_%04d.txt", label, scan_idx);

    FILE *fp = fopen(filename, "w");
    if (!fp) {
        fprintf(stderr, "Failed to open file %s for writing\n", filename);
        return -1;
    }

    fprintf(fp, "# VPR data (%s) for scan %04d\n", label, scan_idx);
    fprintf(fp, "# Format: PointName Reflectivity Height\n");

    fprintf(fp, "ET   %.3f %.3f\n", vpr->ET.reflectivity,   vpr->ET.height);
    fprintf(fp, "BB_u %.3f %.3f\n", vpr->BB_u.reflectivity, vpr->BB_u.height);
    fprintf(fp, "BB_m %.3f %.3f\n", vpr->BB_m.reflectivity, vpr->BB_m.height);
    fprintf(fp, "BB_l %.3f %.3f\n", vpr->BB_l.reflectivity, vpr->BB_l.height);
    fprintf(fp, "CB   %.3f %.3f\n", vpr->CB.reflectivity,   vpr->CB.height);
    fprintf(fp, "GT   %.3f %.3f\n", vpr->GT.reflectivity,   vpr->GT.height);


    fclose(fp);
    return 0;
}



int main(int argc, char *argv[]) {
    // Parse command line arguments
    CommandLineParams cmd_params = parse_command_line(argc, argv);
    
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
    
 //   printf("=== Initializing Test Environment ===\n");
    
    // Initialize everything at once with command line parameters
    initialize_test_environment(
        &VPR_strat, &VPR_conv, &VPR_A_clima, &VPR_A_gmd, &VPR_A_d, &VPR_dummy,
        &params, &raincell, &s_raincell, &cart_grid_res, &sim_time,
        cmd_params.x1, cmd_params.x2, cmd_params.x3, cmd_params.x4, 
        cmd_params.x5, cmd_params.x6
    );
    
//    printf("✓ VPR profiles initialized\n");
//    printf("✓ Raincell and spatial raincell created\n");
//    printf("✓ Radars created and added to list\n");
//    printf("✓ Cart grid resolution: %.0f m\n", cart_grid_res);
//    printf("✓ Simulation time: %.1f minutes\n\n", sim_time);
    
    // =========================================
    // Part 1: Run test_command_centre functionality
    // =========================================
  //  printf("=== Running Command Centre Tests ===\n");
    
    int max_vol_scans = (int)((330.0 - sim_time) / 5);
    for (int i = 0; i < max_vol_scans; i++) {
        generate_commands_file(i, sim_time);
        sim_time += 5.0;
    }
    //printf("✓ Generated %d command files\n", max_vol_scans);
    
    // Start monitoring inputs
    monitor_and_process_inputs(VPR_strat, params, VPR_conv);
    
    // =========================================
    // Part 2: Run test_eval_scan functionality
    // =========================================
    //printf("\n=== Running Eval Scan Tests ===\n");
    
    //#define NUM_SCANS 54
    #define NUM_SCANS 108
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

int print_or_not = 1;
if(print_or_not == 1) {
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_strat.txt", 1, 1);  // Append stratiform with std dev
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_conv.txt", 2, 1);  // Append convective with std dev
}


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


if(print_or_not == 1) {
// --- Write display_grid to file ---
char disp_filename[256];
snprintf(disp_filename, sizeof(disp_filename), "outputs/disp_g_%04d.txt", scan_idx);
if (write_display_grid_to_file(vol, disp_filename) != 0) {
    fprintf(stderr, "Failed to write display grid to %s\n", disp_filename);
}

// --- Write true_grid to file ---
char true_filename[256];
snprintf(true_filename, sizeof(true_filename), "outputs/true_g_%04d.txt", scan_idx);
if (write_true_grid_to_file(vol, true_filename) != 0) {
    fprintf(stderr, "Failed to write true grid to %s\n", true_filename);
}

int xA = vol->num_x/2;
int yA = vol->num_y/2;
//int xA = 20;
//int yA = 20;


char point_height_file[256];
snprintf(point_height_file, sizeof(point_height_file), "outputs/heights_point_%04d.txt", scan_idx);

if (write_heights_for_point(vol, xA, yA, point_height_file) != 0) {
    fprintf(stderr, "Failed to write heights for point (%d,%d)\n", xA, yA);
}

if(scan_idx == 0) write_VPR_to_file(VPR_strat, "strat", scan_idx);
write_VPR_to_file(VPR_conv,  "conv",  scan_idx);
}





        for (int i = 0; i < cg_count; i++)
            free_cart_grid(cart_grids[i]);
        free(cart_grids);
        free_vol_scan(vol);

      //  if (scan_idx % 10 == 0) {
      //      printf("  Processing scan %d/%d...\n", scan_idx + 1, NUM_SCANS);
      //  }
    }
    
    // =========================================
    // Cleanup
    // =========================================
    //printf("\n=== Cleaning Up ===\n");
    cleanup_test_environment(
        VPR_strat, VPR_conv, VPR_A_clima, VPR_A_gmd, VPR_A_d, VPR_dummy,
        params, raincell, s_raincell
    );
    
    //printf("✓ Cleanup complete\n");
  //  printf("✓ Test environment combined successfully!\n");
    
    return 0;
}
