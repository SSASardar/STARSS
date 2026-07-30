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
        .x4 = 0.5,//0.5,         // default: 0.5 ratio
        .x5 = 25000.0,     // default: 25 km from origin
        .x6 = 4.0,//10.0,        // default: 10 (units?)
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
   
   printf("Parameters in order are: %lf, %lf, %lf, %lf, %lf, %lf\n",cmd_params.x1, cmd_params.x2, cmd_params.x3, cmd_params.x4, cmd_params.x5, cmd_params.x6); 
    // =========================================
    // Part 1: Run test_command_centre functionality
    // =========================================
    
    int max_vol_scans = (int)((330.0 - sim_time) / 5);
    for (int i = 0; i < max_vol_scans; i++) {
        generate_commands_file_model_description(i, sim_time);
        sim_time += 5.0;
    }
    
    // Generate the radar data.
    monitor_and_process_inputs_multi_radar(VPR_strat, params, VPR_conv);
    
    // =========================================
    // Part 2: Run test_eval_scan functionality
    // =========================================
    
   #define NUM_SCANS 54
   //RainfallStats stats_array[NUM_SCANS];
  
  // Allocate on heap instead of stack
RainfallStats *stats_array = malloc(NUM_SCANS * sizeof(RainfallStats));
RainfallStats *stats_array_X = malloc(NUM_SCANS * sizeof(RainfallStats));
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
    init_stats_array(stats_array_X, NUM_SCANS);
    init_stats_array(ad_stats_array, NUM_SCANS);

double vpr_emp_strat[120] = {0};
double vpr_emp_conv[120] = {0};

int print_or_not = 1;

    // Determine stats file path based on worker ID
    char stats_path[256];
    char stats_path_X[256];
    char ad_stats_path[256];
    if (cmd_params.worker_id[0] != '\0') {
        snprintf(stats_path, sizeof(stats_path), "outputs_%s/stats.txt", cmd_params.worker_id);
        snprintf(stats_path_X, sizeof(stats_path), "outputs_%s/stats_X.txt", cmd_params.worker_id);
        snprintf(ad_stats_path, sizeof(ad_stats_path), "outputs_%s/ad_stats.txt", cmd_params.worker_id);
    } else {
        snprintf(stats_path, sizeof(stats_path), "outputs/stats.txt");
        snprintf(stats_path_X, sizeof(stats_path_X), "outputs/stats_X.txt");
        snprintf(ad_stats_path, sizeof(ad_stats_path), "outputs/ad_stats.txt");
    }
    
    for (int scan_idx = 0; scan_idx < NUM_SCANS; scan_idx++) {
        char filename[256];
        Vol_scan *vol = NULL;  // Declare vol here
        Vol_scan *vol_1 = NULL;  // Declare vol here
        Cart_grid **cart_grids = NULL;  // Declare cart_grids here
        int cg_count = 0;  // Declare cg_count here
			   //
			   //
			   //

		    // Reset arrays explicitly
    memset(vpr_emp_strat, 0, sizeof(vpr_emp_strat));
    memset(vpr_emp_conv, 0, sizeof(vpr_emp_conv));
	

for (int radar_id = 0; radar_id < MAX_RADARS; radar_id++) {   

	if (cmd_params.worker_id[0] != '\0') {
            snprintf(filename, sizeof(filename), "outputs_%s/radar_%.2d_scan_%04d.txt", cmd_params.worker_id, radar_id,scan_idx);
        } else {
            snprintf(filename, sizeof(filename), "outputs/radar_%.2d_scan_%04d.txt", radar_id,scan_idx);
        }
        if (access(filename, F_OK) == 0) {  // Check if file exists (requires #include <unistd.h>)
            read_radar_scans(filename);
        
        //the the PPI volume scan radars... 
	if(radar_id ==0 || radar_id==1){
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
	
	if(radar_id == 0){
        vol = init_vol_scan(cart_grids, cg_count);
        for (int i = 0; i < cg_count; i++) {
            add_cart_grid_to_volscan(vol, cart_grids[i], i);
        }
	} else if (radar_id == 1) {
	vol_1 = init_vol_scan(cart_grids, cg_count);
        for (int i = 0; i < cg_count; i++) {
            add_cart_grid_to_volscan(vol_1, cart_grids[i], i);
        }
	}
	} else if (radar_id == 3) /*RHI baesd volume scan */ { 
	
		//printf("the scan count for radar %.2d in command %.4d is %.3d\n",radar_id, scan_idx, scan_count);
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
	//process X-band volume scan	
        process_volume_scan_VPR(vol_1);
        compute_average_empVPR(vol_1);
        compute_std_dev_empVPR(vol_1);

	//process C-band volume scan
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


        if (fill_refl_ALA_grid(vol_1, raincell_pos, raincell, VPR_strat, VPR_conv) != 0) {
            exit(EXIT_FAILURE);
        }


        compute_display_grid_KNMI_empirical(vol, -5.0, 0.5, 0);
        compute_display_grid_KNMI_empirical(vol_1, -5.0, 0.5, 0);

        double volume_duration = 5.0 * 60.0;
        if (compute_and_store_stats(vol, -5.0, cart_grid_res, volume_duration, stats_array, scan_idx) == 0) {
            append_stats_to_file(stats_array, scan_idx, stats_path);
        }

if (compute_and_store_stats(vol_1, -5.0, cart_grid_res, volume_duration, stats_array_X, scan_idx) == 0) {
            append_stats_to_file(stats_array_X, scan_idx, stats_path_X);
        }

    // Process adaptive volume scan if empirical VPRs are available
        // Create a deep copy of the volume scan for adaptive processing
if(print_or_not == 1) {
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_strat.txt", 1, 1);  // Append stratiform with std dev
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_conv.txt", 2, 1);  // Append convective with std dev

print_vpr_detailed_with_std(vol_1, "outputs/vpr_emp_strat_X.txt", 1, 1);  // Append stratiform with std dev
print_vpr_detailed_with_std(vol_1, "outputs/vpr_emp_conv_X.txt", 2, 1);  // Append convective with std dev

}
 
if(print_or_not == 1) {
// --- Write display_grid to file ---
char disp_filename[256];
char disp_filename_1[256];
snprintf(disp_filename, sizeof(disp_filename), "outputs/disp_g_%04d.txt", scan_idx);
snprintf(disp_filename_1, sizeof(disp_filename), "outputs/disp_1_g_%04d.txt", scan_idx);
if (write_display_grid_to_file(vol, disp_filename) != 0) {
    fprintf(stderr, "Failed to write display grid to %s\n", disp_filename);
}

if (write_display_grid_to_file(vol_1, disp_filename_1) != 0) {
    fprintf(stderr, "Failed to write display grid to %s\n", disp_filename_1);
}

// --- Write true_grid to file ---
char true_filename[256];
snprintf(true_filename, sizeof(true_filename), "outputs/true_g_%04d.txt", scan_idx);
if (write_true_grid_to_file(vol, true_filename) != 0) {
    fprintf(stderr, "Failed to write true grid to %s\n", true_filename);
}


int xA = vol->num_x/2;
int yA = vol->num_y/2;


char point_height_file[256];
snprintf(point_height_file, sizeof(point_height_file), "outputs/heights_point_%04d.txt", scan_idx);

if (write_heights_for_point(vol, xA, yA, point_height_file) != 0) {
    fprintf(stderr, "Failed to write heights for point (%d,%d)\n", xA, yA);
}

if(scan_idx == 0) write_VPR_to_file(VPR_strat, "strat", scan_idx);
write_VPR_to_file(VPR_conv,  "conv",  scan_idx);
}





//}    
	    
//	    memcpy(vol->emp_vpr_strat, vpr_emp_strat, 120 * sizeof(double));
//	    memcpy(vol->emp_vpr_conv, vpr_emp_conv, 120 * sizeof(double));

combine_vpr_M1(vol, vpr_emp_strat, vpr_emp_conv);


if(print_or_not == 1) {
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_strat_ad.txt", 1, 1);  // Append stratiform with std dev
print_vpr_detailed_with_std(vol, "outputs/vpr_emp_conv_ad.txt", 2, 1);  // Append convective with std dev

print_vpr_interpolated(VPR_strat, "outputs/vpr_true_strat.txt", 1); 
print_vpr_interpolated(VPR_conv, "outputs/vpr_true_conv.txt", 1); 
}

 
                        compute_display_grid_KNMI_empirical(vol, -5.0, 0.5, 0);

if(print_or_not == 1) {
// --- Write display_grid to file ---
char disp_filename[256];
snprintf(disp_filename, sizeof(disp_filename), "outputs/ad_disp_g_%04d.txt", scan_idx);
if (write_display_grid_to_file(vol, disp_filename) != 0) {
    fprintf(stderr, "Failed to write display grid to %s\n", disp_filename);
}

}

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
    free(stats_array_X);
    free(ad_stats_array);

    cleanup_test_environment(
        VPR_strat, VPR_conv, VPR_A_clima, VPR_A_gmd, VPR_A_d, VPR_dummy,
        params, raincell, s_raincell
    );
    
    return 0;
}
