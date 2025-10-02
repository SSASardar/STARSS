#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "radars.h"
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "common.h"
#include <time.h>
#include "processing.h"
#include <stdbool.h>
#include <float.h>
#include "vertical_profiles.h"


int main() {
    clock_t start = clock();
    
    read_radar_scans("outputs/radar_scans.txt");

    printf("Loaded %d radar scans:\n", scan_count);
    for (int i = 0; i < scan_count; ++i) {
/*        RadarScan* s = &radar_scans[i];
        printf("Scan %d: TIME in mins (%lf)  Radar ID %d, Grid[0]=%.2f\n",
               s->scan_index,s->time, s->radar->id,
               s->box->grid ? s->box->grid[65] : -1.0);
  */  }

    // -------------------------------
    // Define Cartesian grid resolution
    double cart_grid_res = 25;
/*
    // Step 1: allocate space for Cart_grids
    Cart_grid *cart_grids = malloc(scan_count * sizeof(Cart_grid));
    if (!cart_grids) {
        fprintf(stderr, "Failed to allocate cart_grids\n");
        return 1;
    }
*/



Cart_grid **cart_grids = malloc(scan_count * sizeof(Cart_grid*));
if (!cart_grids) {
    fprintf(stderr, "Failed to allocate cart_grids array\n");
    return 1;
}





// defining VPR:
//
VPR_params *params = malloc(sizeof(VPR_params));
init_VPR_params(params);
fill_VPR_params(params,
    60.0*60, 120.0*60.0, 170.0*60.0, 200.0*60.0, 230.0*60.0,
    10.0, 8000.0, 2000.0,        // Echo top
    50.0, 3.0, 2.0, 2.0,         // Bright band Z
    3000.0, 100.0, 50.0,         // Bright band heights
    25.0, 4.0, 3.0,              // Width Z
    1000.0, 4500.0, 750.0,       // Width H
    0.4, -0.2, -0.15, -0.05,     // Ratio
    35, -3.0, 2.0, 20.0,         // Cell base Z
    500.0, 150.0, 25.0           // Cell base heights
);

VPR *VPR_strat   = create_and_fill_VPR(params);
    VPR *VPR_conv  = create_VPR();

    VPR *VPR_A_clima =create_VPR();
    VPR *VPR_A_gmd  =create_VPR();
  

    VPR *VPR_A_d = create_VPR();

    VPR *VPR_dummy = create_VPR();
    
    double t1,t2, t3, timeB;
    t1 = params->t_growth_start;
    t2 = params->t_decay_end;
    t3 = params->t_mature_end;
 
compute_climatology_VPR(VPR_A_clima,params,60.0,70.0 * 60.0, VPR_dummy); 
compute_average_VPR(VPR_A_gmd, params, t1, t2, 60.0, VPR_dummy);
compute_average_VPR(VPR_A_d,   params, t3, t2, 60.0, VPR_dummy);



    int cg_count = 0;

    // Step 2: convert Polar_box → Cart_grid
    for (int i = 0; i < scan_count; ++i) {
        Polar_box* p_box = radar_scans[i].box;
        Radar* radar     = radar_scans[i].radar;
	double time 	 = radar_scans[i].time;
       //update the convective profile. 
      
       double time_in_secs_1 = time*60.0;	
	update_VPR(VPR_strat, params, time_in_secs_1, VPR_conv);



	// Build bounding box
        Bounding_box* bbox = bounding_box_from_textfile(p_box, radar);

        int num_x = (int)fabs(ceil((bbox->bottomLeft.x)/cart_grid_res) 
                              - floor((bbox->bottomRight.x)/cart_grid_res));
        int num_y = (int)fabs(ceil((bbox->bottomLeft.y)/cart_grid_res) 
                              - floor((bbox->topLeft.y)/cart_grid_res));

        Point ref_point;
        ref_point.x = ceil((bbox->bottomLeft.x)/cart_grid_res) * cart_grid_res;
        ref_point.y = ceil((bbox->bottomLeft.y)/cart_grid_res) * cart_grid_res;

        Cart_grid *cg = Cart_grid_init(cart_grid_res, num_x, num_y, ref_point);
        if (!cg) continue;

        Point p;
        double c_x = radar->x;
        double c_y = radar->y;
        int range_idx, angle_idx;

        for (int xi = 0; xi < num_x; xi++) {
            p.x = ref_point.x + xi * cart_grid_res;
            for (int yi = 0; yi < num_y; yi++) {
                int idA = xi * num_y + yi;
                p.y = ref_point.y + yi * cart_grid_res;

                if (getPolarBoxIndex(p, c_x, c_y, p_box, &range_idx, &angle_idx)) {
                    int p_grid_idx = range_idx * (int)(p_box->num_angles) + angle_idx;
                    cg->height_grid[idA]  = p_box->height_grid[p_grid_idx];
                    //cg->grid[idA]         = p_box->grid[p_grid_idx];
                    
		    if (p_box->grid[p_grid_idx] == 0) {
			    cg->grid[idA] = p_box->grid[p_grid_idx];
		    } else if (p_box->grid[p_grid_idx] == 1) {
			    cg->grid[idA] = get_reflectivity_at_height(VPR_strat, p_box->height_grid[p_grid_idx]);
		    } else if (p_box->grid[p_grid_idx] == 2) {
			   // cg->grid[idA] = get_reflectivity_at_height(VPR_A_d, p_box->height_grid[p_grid_idx]);
			    cg->grid[idA] = get_reflectivity_at_height(VPR_conv, p_box->height_grid[p_grid_idx]);
		    }

/*		 if (p_box->grid[p_grid_idx] == 0) {
			    cg->grid[idA] = p_box->grid[p_grid_idx];
		    } else {
			    cg->grid[idA] = get_reflectivity_at_height(VPR_A_clima, p_box->height_grid[p_grid_idx]);
		    }
*/		    
		    cg->attenuation_grid[3*idA+0] = p_box->attenuation_grid[3*p_grid_idx+0];
                    cg->attenuation_grid[3*idA+1] = p_box->attenuation_grid[3*p_grid_idx+1];
                    cg->attenuation_grid[3*idA+2] = p_box->attenuation_grid[3*p_grid_idx+2];
                } else {
                    cg->grid[idA]         = NAN;
                    cg->height_grid[idA]  = NAN;
                    cg->attenuation_grid[3*idA+0] = NAN;
                    cg->attenuation_grid[3*idA+1] = NAN;
                    cg->attenuation_grid[3*idA+2] = NAN;
                }
            }
        }

        cart_grids[cg_count++] = cg;
    }

    // Step 3: initialize Vol_scan (once you have all Cart_grids)
    Vol_scan *vol = init_vol_scan(cart_grids, cg_count);
    if (!vol) {
        fprintf(stderr, "Failed to init volume scan\n");
        return 1;
    }

    // Step 4: add each Cart_grid into the Vol_scan
    for (int i = 0; i < cg_count; i++) {
        add_cart_grid_to_volscan(vol, cart_grids[i], i);
    }

    printf("Volume scan created: %d PPIs, %zu x %zu grid, %zu elements\n",
           vol->num_PPIs, vol->num_x, vol->num_y, vol->num_elements);

/*
    // Example: inspect one point
    int test_x = 1500, test_y = 1000, test_ppi = 10;
    int idx = test_ppi * vol->num_elements + test_y * vol->num_x + test_x;
    if (idx < vol->num_elements * vol->num_PPIs) {
        printf("Sample VPR point: refl=%.2f, h=%.2f\n",
               vol->grid_refl[idx],
               vol->grid_height[idx]);
    }


//    write_vol_scan_ppi_to_file(vol, 1, "outputs/ppi1.txt");

for (int ppi_idx = 0; ppi_idx < scan_count; ppi_idx++) {
    char filename[256];  // buffer for filename
    snprintf(filename, sizeof(filename), "outputs/ppi%d.txt", ppi_idx);
    write_vol_scan_ppi_to_file(vol, ppi_idx, filename);
}
*/


compute_display_grid_max(vol,10.0);
write_display_grid_to_file(vol, "outputs/disp_grid_max.txt");



// calculate true raincell:
double true_time_min = radar_scans[scan_count-1].time + ( radar_scans[scan_count-1].time -  radar_scans[scan_count-2].time  );
   double true_time = true_time_min * 60.0;
    Raincell* raincell = create_raincell(1, 0.5, 10000.0, -0.5);   
Spatial_raincell* s_raincell = create_spatial_raincell(1, -120000.0,80000.0, 6);
	

	update_VPR(VPR_strat, params, true_time, VPR_conv);




// initialize your cell, e.g. my_cell.initial_x, my_cell.dx, etc.

Point* raincell_pos = get_position_raincell(true_time, s_raincell);
if (!raincell_pos) {
    fprintf(stderr, "Failed to get raincell position\n");
    exit(EXIT_FAILURE);
}
//printf("Raincell position: x=%f, y=%f\n", raincell_pos->x, raincell_pos->y);


if (fill_refl_ALA_grid(vol, raincell_pos, raincell, VPR_strat, VPR_conv) != 0) {
    fprintf(stderr, "Failed to fill Refl_ALA grid\n");
}


write_true_grid_to_file(vol, "outputs/disp_grid_true.txt");


    double mse, mae, bias;

    int ret = compute_rainfall_statistics(vol,10.0, &mse, &mae, &bias);
    if (ret == 0) {
        printf("MSE: %.5f\n", mse);
        printf("MAE: %.5f\n", mae);
        printf("Bias: %.5f\n", bias);
    } else {
        printf("Error computing statistics: %d\n", ret);
    }


/*
    // Step 5: cleanup
    free_vol_scan(vol);
    free(cart_grids);
*/

for (int i = 0; i < cg_count; i++) {
    free_cart_grid(cart_grids[i]);
}
free(cart_grids);

free_vol_scan(vol);

    clock_t end = clock();
    printf("Time taken: %f seconds\n", (double)(end - start) / CLOCKS_PER_SEC);

    return 0;
}

