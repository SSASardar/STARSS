#include "common.h"
#include "radars.h"
#include "processing.h"
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "vertical_profiles.h"

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <stdbool.h>
#include <float.h>


#define NUM_SCANS 54  // 0..53
    
typedef struct {
    double mse;
    double mae;
    double bias;
    double total_measured;        // sum of R over grid points
    double total_true;            // sum of R over grid points
    double total_measured_mm2;    // area-corrected total in mm*h per km²
    double total_true_mm2;        // area-corrected total in mm*h per km²
} RainfallStats;

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

    fclose(fp);
    return 0;
}




int main() {
    clock_t start = clock();

    RainfallStats stats_array[NUM_SCANS];

    // -------------------------------
    // Step 0: setup VPR structures once
    VPR_params *params = malloc(sizeof(VPR_params));
    init_VPR_params(params);
    fill_VPR_params(params,
        120.0*60, 180.0*60.0, 230.0*60.0, 260.0*60.0, 290.0*60.0,
        10.0, 8000.0, 2000.0,
        50.0, 3.0, 2.0, 2.0,
        3000.0, 100.0, 50.0,
        25.0, 4.0, 3.0,
        1000.0, 4500.0, 750.0,
        0.4, -0.2, -0.15, -0.05,
        35, -3.0, 2.0, 20.0,
        500.0, 150.0, 25.0
    );

    VPR *VPR_strat   = create_and_fill_VPR(params);
    VPR *VPR_conv    = create_VPR();
    VPR *VPR_dummy   = create_VPR();
    VPR *VPR_A_clima = create_VPR();
    VPR *VPR_A_gmd   = create_VPR();
    VPR *VPR_A_d     = create_VPR();

    double t1 = params->t_growth_start;
    double t2 = params->t_decay_end;
    double t3 = params->t_mature_end;

    compute_climatology_VPR(VPR_A_clima, params, 60.0, 70.0*60.0, VPR_dummy);
    compute_average_VPR(VPR_A_gmd, params, t1, t2, 60.0, VPR_dummy);
    compute_average_VPR(VPR_A_d, params, t3, t2, 60.0, VPR_dummy);


    Raincell* raincell = create_raincell(1, 0.5, 10000.0, -0.5);   
Spatial_raincell* s_raincell = create_spatial_raincell(1, -80000.0,80000.0,3);

    double cart_grid_res = 25;

    for (int scan_idx = 0; scan_idx < NUM_SCANS; scan_idx++) {
    char filename[256];
    snprintf(filename, sizeof(filename), "outputs/radar_scan_%04d.txt", scan_idx);

    read_radar_scans(filename);
    if (scan_count == 0) {
        fprintf(stderr, "No radar scans loaded from %s\n", filename);
        continue;
    }

    printf("Processing %s (scan %d/%d)...\n", filename, scan_idx+1, NUM_SCANS);

    // Allocate cart_grids for this scan
    Cart_grid **cart_grids = malloc(scan_count * sizeof(Cart_grid*));
    if (!cart_grids) { fprintf(stderr, "Malloc failed\n"); exit(1); }

    int cg_count = 0;

    for (int i = 0; i < scan_count; i++) {
        Polar_box* p_box = radar_scans[i].box;
        Radar* radar = radar_scans[i].radar;
        double time = radar_scans[i].time;
	double time_s_2 = time*60;
        update_VPR(VPR_strat, params, time_s_2, VPR_conv);

        Bounding_box* bbox = bounding_box_from_textfile(p_box, radar);

        int num_x = (int)(ceil((bbox->bottomRight.x - bbox->bottomLeft.x)/cart_grid_res));
        int num_y = (int)(ceil((bbox->topLeft.y - bbox->bottomLeft.y)/cart_grid_res));
        if (num_x <= 0) num_x = 1;
        if (num_y <= 0) num_y = 1;

        Point ref_point = {
            ceil(bbox->bottomLeft.x / cart_grid_res) * cart_grid_res,
            ceil(bbox->bottomLeft.y / cart_grid_res) * cart_grid_res
        };

        Cart_grid *cg = Cart_grid_init(cart_grid_res, num_x, num_y, ref_point);
        if (!cg) continue;

        for (int xi = 0; xi < num_x; xi++) {
            for (int yi = 0; yi < num_y; yi++) {
                int idA = xi * num_y + yi;
                Point p = {ref_point.x + xi*cart_grid_res, ref_point.y + yi*cart_grid_res};
                int range_idx, angle_idx;

                if (getPolarBoxIndex(p, radar->x, radar->y, p_box, &range_idx, &angle_idx)) {
                    int p_grid_idx = range_idx * (int)p_box->num_angles + angle_idx;
                    cg->height_grid[idA] = p_box->height_grid[p_grid_idx];
                    cg->grid[idA] = p_box->grid[p_grid_idx];
                    cg->attenuation_grid[idA] = p_box->attenuation_grid[p_grid_idx];
                } else {
                    cg->grid[idA] = NAN;
                    cg->height_grid[idA] = NAN;
	            cg->attenuation_grid[idA] = NAN;
                }
            }
        }

        cart_grids[cg_count++] = cg;
    }

    Vol_scan *vol = init_vol_scan(cart_grids, cg_count);
    for (int i = 0; i < cg_count; i++)
        add_cart_grid_to_volscan(vol, cart_grids[i], i);

//compute_display_grid_max(vol,10.0);
compute_display_grid_lowest_valid_height(vol,10.0);
//compute_display_grid_min_above_threshold(vol,10.0);
    double true_time_min = radar_scans[scan_count-1].time +
                           (radar_scans[scan_count-1].time - radar_scans[scan_count-2].time);
    double true_time = true_time_min * 60.0;

    update_VPR(VPR_strat, params, true_time, VPR_conv);

    Point* raincell_pos = get_position_raincell(true_time, s_raincell);
    if (!raincell_pos) {
        fprintf(stderr, "Failed to get raincell position\n");
        exit(EXIT_FAILURE);
    }

    if (fill_refl_ALA_grid(vol, raincell_pos, raincell, VPR_strat, VPR_conv) != 0) {
        fprintf(stderr, "Failed to fill Refl_ALA grid\n");
    }


double mse, mae, bias;
double total_measured, total_true_masked, total_measured_mm2, total_true_mm2;
double total_true_unmasked, total_true_mm2_unmasked;

if (compute_rainfall_statistics(vol, 10.0, cart_grid_res,
                                &mse, &mae, &bias,
                                &total_measured, &total_true_masked,
                                &total_measured_mm2, &total_true_mm2,
                                &total_true_unmasked, &total_true_mm2_unmasked) == 0) {
    stats_array[scan_idx].mse = mse;
    stats_array[scan_idx].mae = mae;
    stats_array[scan_idx].bias = bias;
    stats_array[scan_idx].total_measured = total_measured;
    // store the **unmasked** true rainfall instead of masked
    stats_array[scan_idx].total_true = total_true_unmasked;

    double time_for_volume_scan = 5.0 * 60.0; // seconds

    stats_array[scan_idx].total_measured_mm2 = total_measured_mm2 / time_for_volume_scan;
    stats_array[scan_idx].total_true_mm2 = total_true_mm2_unmasked / time_for_volume_scan;
} else {
    stats_array[scan_idx].mse = stats_array[scan_idx].mae = stats_array[scan_idx].bias = NAN;
    stats_array[scan_idx].total_measured = stats_array[scan_idx].total_true = NAN;
    stats_array[scan_idx].total_measured_mm2 = stats_array[scan_idx].total_true_mm2 = NAN;
}

// Print stats for this scan
printf("Scan %d stats: MSE=%.5f MAE=%.5f Bias=%.5f "
       "Total_meas=%.5f Total_true(unmasked)=%.5f "
       "Total_meas_mm2=%.5f Total_true_mm2(unmasked)=%.5f\n",
       scan_idx,
       stats_array[scan_idx].mse, stats_array[scan_idx].mae, stats_array[scan_idx].bias,
       stats_array[scan_idx].total_measured, stats_array[scan_idx].total_true,
       stats_array[scan_idx].total_measured_mm2, stats_array[scan_idx].total_true_mm2);

FILE *fp = fopen("outputs/stats.txt", "a");
if (fp) {
    if (scan_idx == 0)
        fprintf(fp, "Scan MSE MAE Bias Total_meas Total_true_unmasked Total_meas_mm2 Total_true_mm2_unmasked\n");
    fprintf(fp, "%d %.5f %.5f %.5f %.5f %.5f %.5f %.5f\n",
            scan_idx,
            stats_array[scan_idx].mse, stats_array[scan_idx].mae, stats_array[scan_idx].bias,
            stats_array[scan_idx].total_measured, stats_array[scan_idx].total_true,
            stats_array[scan_idx].total_measured_mm2, stats_array[scan_idx].total_true_mm2);
    fclose(fp);
} else {
    fprintf(stderr, "Failed to open outputs/stats.txt for writing\n");
}

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

//int xA = vol->num_x/2;
//int yA = vol->num_y/2;
int xA = 450;
int yA = 300;


char point_height_file[256];
snprintf(point_height_file, sizeof(point_height_file), "outputs/heights_point_%04d.txt", scan_idx);

if (write_heights_for_point(vol, xA, yA, point_height_file) != 0) {
    fprintf(stderr, "Failed to write heights for point (%d,%d)\n", xA, yA);
}

if(scan_idx == 0) write_VPR_to_file(VPR_strat, "strat", scan_idx);
write_VPR_to_file(VPR_conv,  "conv",  scan_idx);

    // Free memory
    for (int i = 0; i < cg_count; i++)
        free_cart_grid(cart_grids[i]);
    free(cart_grids);
    free_vol_scan(vol);
}
    clock_t end = clock();
    printf("Total time: %f seconds\n", (double)(end - start)/CLOCKS_PER_SEC);

    return 0;
}

