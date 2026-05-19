// Combines both test_command_centre and test_eval_scan functionality

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <getopt.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>
#include <unistd.h>


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
    char worker_id[16];  // worker ID for parallel execution
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
    printf("  -w, --worker-id <id>        Worker ID for parallel execution (creates isolated directories)\n");
    printf("  -h, --help                  Show this help message\n");
    printf("\nExample:\n");
    printf("  %s -r 500 -m 180 -c 600 -k 0.7 -y 75000 -a 12\n", program_name);
    printf("  %s -r 500 -m 180 -c 600 -k 0.7 -y 75000 -a 12 -w 3\n", program_name);
}

CommandLineParams parse_command_line(int argc, char *argv[]) {
    CommandLineParams params = {
        .x1 = 1000.0,      // default: 1 km resolution
        .x2 = 170.0,       // default: 170 minutes
        .x3 = 500.0,       // default: 500 m cloud base
        .x4 = 0.5,         // default: 0.5 ratio
        .x5 = 80000.0,     // default: 80 km
        .x6 = 10.0,        // default: 10 (units?)
        .worker_id = ""     // default: empty (original behavior)
    };
    
    static struct option long_options[] = {
        {"resolution",      required_argument, 0, 'r'},
        {"mature-end",      required_argument, 0, 'm'},
        {"cloud-base",      required_argument, 0, 'c'},
        {"core-ratio",      required_argument, 0, 'k'},
        {"y-distance",      required_argument, 0, 'y'},
        {"apparent-motion", required_argument, 0, 'a'},
        {"worker-id",       required_argument, 0, 'w'},
        {"help",            no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };
    
    int opt;
    int option_index = 0;
    
    while ((opt = getopt_long(argc, argv, "r:m:c:k:y:a:w:h", long_options, &option_index)) != -1) {
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
            case 'w':
                snprintf(params.worker_id, sizeof(params.worker_id), "%s", optarg);
                break;
            case 'h':
                print_usage(argv[0]);
                exit(EXIT_SUCCESS);
            default:
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
        }
    }
    
    return params;
}

// Helper function to create worker-specific directories
void create_worker_directories(const char *worker_id) {
    char path[256];
    
    // Create outputs directory
    if (worker_id && worker_id[0]) {
        snprintf(path, sizeof(path), "outputs_%s", worker_id);
    } else {
        snprintf(path, sizeof(path), "outputs");
    }
    if (mkdir(path, 0755) == -1 && errno != EEXIST) {
        fprintf(stderr, "Warning: Could not create directory %s: %s\n", path, strerror(errno));
    }
    
    // Create inputs directory
    if (worker_id && worker_id[0]) {
        snprintf(path, sizeof(path), "inputs_%s", worker_id);
    } else {
        snprintf(path, sizeof(path), "inputs");
    }
    if (mkdir(path, 0755) == -1 && errno != EEXIST) {
        fprintf(stderr, "Warning: Could not create directory %s: %s\n", path, strerror(errno));
    }
    
    // Create archive directory
    if (worker_id && worker_id[0]) {
        snprintf(path, sizeof(path), "archive_%s", worker_id);
    } else {
        snprintf(path, sizeof(path), "archive");
    }
    if (mkdir(path, 0755) == -1 && errno != EEXIST) {
        fprintf(stderr, "Warning: Could not create directory %s: %s\n", path, strerror(errno));
    }
}

int main(int argc, char *argv[]) {
    // Parse command line arguments
    CommandLineParams cmd_params = parse_command_line(argc, argv);
    
    // Set worker ID if provided
    if (cmd_params.worker_id[0] != '\0') {
        set_worker_id(cmd_params.worker_id);
        printf("Worker ID set to: %s\n", cmd_params.worker_id);
    }
    
    // Create worker-specific directories
    create_worker_directories(cmd_params.worker_id);
    
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
    
    // Initialize everything at once with command line parameters
    initialize_test_environment(
        &VPR_strat, &VPR_conv, &VPR_A_clima, &VPR_A_gmd, &VPR_A_d, &VPR_dummy,
        &params, &raincell, &s_raincell, &cart_grid_res, &sim_time,
        cmd_params.x1, cmd_params.x2, cmd_params.x3, cmd_params.x4, 
        cmd_params.x5, cmd_params.x6
    );
    
    // =========================================
    // Part 1: Run test_command_centre functionality
    // =========================================
    
    int max_vol_scans = (int)((330.0 - sim_time) / 5);
    for (int i = 0; i < max_vol_scans; i++) {
        generate_commands_file_vol_rhi_A(i, sim_time);
        sim_time += 5.0;
    }
    
    // Start monitoring inputs
    monitor_and_process_inputs_multi_radar(VPR_strat, params, VPR_conv);
    
    // =========================================
    // Part 2: Run test_eval_scan functionality
    // =========================================
    
   #define NUM_SCANS 54
   //RainfallStats stats_array[NUM_SCANS];
  
  // Allocate on heap instead of stack
RainfallStats *stats_array = malloc(NUM_SCANS * sizeof(RainfallStats));
RainfallStats *ad_stats_array = malloc(NUM_SCANS * sizeof(RainfallStats));
if (!ad_stats_array) {
    fprintf(stderr, "ERROR: Failed to allocate stats_array for %d scans\n", NUM_SCANS);
    return 1;
}
if (!stats_array) {
    fprintf(stderr, "ERROR: Failed to allocate stats_array for %d scans\n", NUM_SCANS);
    return 1;
}
  
    init_stats_array(stats_array, NUM_SCANS);
    init_stats_array(ad_stats_array, NUM_SCANS);

double vpr_emp_strat[120] = {0};
double vpr_emp_conv[120] = {0};



    // Determine stats file path based on worker ID
    char stats_path[256];
    char ad_stats_path[256];
    if (cmd_params.worker_id[0] != '\0') {
        snprintf(stats_path, sizeof(stats_path), "outputs_%s/stats.txt", cmd_params.worker_id);
        snprintf(ad_stats_path, sizeof(ad_stats_path), "outputs_%s/ad_stats.txt", cmd_params.worker_id);
    } else {
        snprintf(stats_path, sizeof(stats_path), "outputs/stats.txt");
        snprintf(ad_stats_path, sizeof(ad_stats_path), "outputs/ad_stats.txt");
    }
    
    for (int scan_idx = 0; scan_idx < NUM_SCANS; scan_idx++) {
        char filename[256];
        Vol_scan *vol = NULL;  // Declare vol here
        Cart_grid **cart_grids = NULL;  // Declare cart_grids here
        int cg_count = 0;  // Declare cg_count here
			   //
			   //
			   //

for (int radar_id = 0; radar_id < MAX_RADARS; radar_id++) {   

	if (cmd_params.worker_id[0] != '\0') {
            snprintf(filename, sizeof(filename), "outputs_%s/radar_%.2d_scan_%04d.txt", cmd_params.worker_id, radar_id,scan_idx);
        } else {
            snprintf(filename, sizeof(filename), "outputs/radar_%.2d_scan_%04d.txt", radar_id,scan_idx);
        }
        if (access(filename, F_OK) == 0) {  // Check if file exists (requires #include <unistd.h>)
            read_radar_scans(filename);
        
        
	if(radar_id ==0){
	if (scan_count == 0) continue;

        cart_grids = malloc(scan_count * sizeof(Cart_grid*));
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

        vol = init_vol_scan(cart_grids, cg_count);
        for (int i = 0; i < cg_count; i++) {
            add_cart_grid_to_volscan(vol, cart_grids[i], i);
        }
	} else if (radar_id == 3) {
printf("the scan count for radar %.2d in command %.4d is %.3d\n",radar_id, scan_idx, scan_count);
        cart_grids = malloc(scan_count * sizeof(Cart_grid*));
        if (!cart_grids) exit(1);

        int cg_count = 0;

	init_polar_vpr_arrays(vpr_emp_strat, vpr_emp_conv);
        for (int i = 0; i < scan_count; i++) {
            Polar_box* p_box = radar_scans[i].box;
            Radar* radar = radar_scans[i].radar;
            double time = radar_scans[i].time;
            double time_s_2 = time * 60;
		        if (p_box != NULL) {
            process_polar_box_for_vpr(p_box, vpr_emp_strat, vpr_emp_conv);
        }
//            update_VPR(VPR_strat, params, time_s_2, VPR_conv);

//            Cart_grid *cg = interpolate_scan_NN_RHI(p_box, radar, time, cart_grid_res, scan_idx, i);
//            if (cg) cart_grids[cg_count++] = cg;
        }

    // Compute averages (will be stored back into indices 40-79)
    compute_polar_vpr_averages_inplace(vpr_emp_strat);
    compute_polar_vpr_averages_inplace(vpr_emp_conv);
    
    // SECOND PASS: Compute sum of squared differences for standard deviation
    for (int s = 0; s < scan_count; s++) {
        Polar_box* box = radar_scans[s].box;
        if (box != NULL) {
            process_polar_box_for_std_dev(box, vpr_emp_strat);
            process_polar_box_for_std_dev(box, vpr_emp_conv);
        }
    }
    
    // Compute final standard deviations (stored back into indices 80-119)
    compute_polar_vpr_std_dev_inplace(vpr_emp_strat);
    compute_polar_vpr_std_dev_inplace(vpr_emp_conv);
    
	}
	}
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
            append_stats_to_file(stats_array, scan_idx, stats_path);
        }

    // Process adaptive volume scan if empirical VPRs are available
        // Create a deep copy of the volume scan for adaptive processing
 	    int print_or_not = 1;
if(print_or_not == 1) {
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_strat.txt", 1, 1);  // Append stratiform with std dev
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_conv.txt", 2, 1);  // Append convective with std dev
}
     
	    
//	    memcpy(vol->emp_vpr_strat, vpr_emp_strat, 120 * sizeof(double));
//	    memcpy(vol->emp_vpr_conv, vpr_emp_conv, 120 * sizeof(double));

combine_vpr_M1(vol, vpr_emp_strat, vpr_emp_conv);


if(print_or_not == 1) {
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_strat_ad.txt", 1, 1);  // Append stratiform with std dev
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_conv_ad.txt", 2, 1);  // Append convective with std dev

print_vpr_interpolated(VPR_strat, "outputs/vpr_true_strat.txt", 1); 
print_vpr_interpolated(VPR_conv, "outputs/vpr_true_conv.txt", 1); 
}

 
            // Process adaptive volume scan (you may need to re-run some steps with empirical VPRs)
            //process_volume_scan_VPR(ad_vol);
            //compute_average_empVPR(ad_vol);
            //compute_std_dev_empVPR(ad_vol);
                        compute_display_grid_KNMI_empirical(vol, -5.0, 0.5, 0);
            
            // Compute and store adaptive statistics
            if (compute_and_store_stats(vol, -5.0, cart_grid_res, volume_duration, ad_stats_array, scan_idx) == 0) {
                append_stats_to_file(ad_stats_array, scan_idx, ad_stats_path);
            }

        for (int i = 0; i < cg_count; i++)
            free_cart_grid(cart_grids[i]);
        free(cart_grids);
        free_vol_scan(vol);
    }
    
    // =========================================
    // Cleanup
    // =========================================
    free(stats_array);
    free(ad_stats_array);

    cleanup_test_environment(
        VPR_strat, VPR_conv, VPR_A_clima, VPR_A_gmd, VPR_A_d, VPR_dummy,
        params, raincell, s_raincell
    );
    
    return 0;
}
