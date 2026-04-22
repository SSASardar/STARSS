#include <stdio.h>                                   
#include <math.h>
#include <stdlib.h>
#include "radars.h"
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "common.h"
#include <time.h>
#include "processing.h"
#include<stdbool.h>
#include <float.h>
#include "vertical_profiles.h"

int main() {
	clock_t start = clock();
    
	read_radar_scans("outputs/radar_scans.txt");

    printf("Loaded %d radar scans:\n", scan_count);
    for (int i = 0; i < scan_count; ++i) {
        RadarScan* s = &radar_scans[i];
        printf("Scan %d: Radar ID %d, Grid[0]=%.2f\n",
               s->scan_index, s->radar->id,
               s->box->grid ? s->box->grid[65] : -1.0);
    }

// Defining the cartesian grid resolution:

    double cart_grid_res = 50.0;
	int num_x, num_y;
int target_radar_id = 1;


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





for (int i = 0; i < scan_count; ++i) {
    if (radar_scans[i].radar->id == target_radar_id) {
        Polar_box* p_box = radar_scans[i].box;
        Radar* radar = radar_scans[i].radar;
	print_polar_box(p_box);
	printf("Scan %d: First grid value: %.2f\n", 
               radar_scans[i].scan_index, p_box->grid[0]);

 	// create bounding box for the polar box
	
	Bounding_box* bbox = bounding_box_from_textfile(p_box, radar);	
	print_bounding_box(bbox); 

	// Initialising the cartesian grid structure:	
	num_x = (int)fabs(ceil((bbox->bottomLeft.x)/cart_grid_res) - floor((bbox->bottomRight.x)/cart_grid_res));
	num_y = (int)fabs(ceil((bbox->bottomLeft.y)/cart_grid_res) - floor((bbox->topLeft.y)/cart_grid_res));
	Point ref_point;
	ref_point.x = ceil((bbox->bottomLeft.x)/cart_grid_res)*cart_grid_res;
	ref_point.y = ceil((bbox->bottomLeft.y)/cart_grid_res)*cart_grid_res;
	printf("ref_point = (%.2lf, %.2lf)\n\n", ref_point.x, ref_point.y);
 	Cart_grid* cg = Cart_grid_init(cart_grid_res, num_x, num_y, ref_point);
	
	printf("there are %d num_x and %d num_y\n", cg->num_x, cg->num_y);
	printf("There are %d elements in the cartesian grid \n",cg->num_elements);
    
    	Point p;
	double c_x = radar->x;
	double c_y = radar->y;
	p_box->x = radar->x;
	p_box->y = radar->y;
	p_box->z = radar->z;
	int range_idx, angle_idx;
	int idA;
	for(int xi = 0; xi<num_x;xi++){
		p.x = ref_point.x + xi*cart_grid_res;		
		for(int yi = 0; yi<num_y;yi++){
			idA = xi*num_y+yi;
			p.y = ref_point.y + yi*cart_grid_res;		
			if (getPolarBoxIndex(p, c_x, c_y, p_box, &range_idx, &angle_idx)) {
			    int p_grid_idx = range_idx * (int)(p_box->num_angles) + angle_idx;
			    cg->height_grid[idA] = p_box->height_grid[p_grid_idx];
			    //cg->grid[idA] = p_box->grid[p_grid_idx];

            // Debugging: Check p_box height
            if (p_box->height_grid[p_grid_idx] == 0) {
                printf("DEBUG: scan %d, polar grid height zero at (range_idx=%d, angle_idx=%d)\n",
                        radar_scans[i].scan_index, range_idx, angle_idx);
            }


			    if (p_box->grid[p_grid_idx] == 0) {
			    cg->grid[idA] = p_box->grid[p_grid_idx];
			    } else {
			    cg->grid[idA] = get_reflectivity_at_height(VPR_strat, p_box->height_grid[p_grid_idx]);
			    }

            // Debugging: Check cartesian grid height
            if (cg->height_grid[idA] == 0) {
                printf("DEBUG: scan %d, cart grid height zero at (xi=%d, yi=%d)\n",
                        radar_scans[i].scan_index, xi, yi);
            }


			    cg->estimated_attenuation_grid[3*(idA)+0] =p_box->attenuation_grid[3*p_grid_idx + 0];
			    cg->estimated_attenuation_grid[3*(idA)+1] =p_box->attenuation_grid[3*p_grid_idx + 1];
			    cg->estimated_attenuation_grid[3*(idA)+2] =p_box->attenuation_grid[3*p_grid_idx + 2]; 

			} else {
			    cg->grid[idA] = NAN;// Handle point outside polar box
			    cg->height_grid[idA] = NAN;// Handle point outside polar box
			    cg->estimated_attenuation_grid[3*(idA)+0] =-1.0; 
			    cg->estimated_attenuation_grid[3*(idA)+1] =-1.0; 
			    cg->estimated_attenuation_grid[3*(idA)+2] =-1.0; 
			}
		}
	}
 //for (int k = 0; k<3;k++)   writeCartGridToFile(cg,i,k);
      writeCartGridToFile(cg,i,0);

    }

}

    clock_t end = clock();

    double time_taken = (double)(end - start) / CLOCKS_PER_SEC;

    printf("Time taken: %f seconds\n", time_taken);


    // Free memory
    for (int i = 0; i < radar_count; ++i)
        free(radar_list[i]);
    
	for (int i = 0; i < scan_count; ++i)
        free(radar_scans[i].box->grid), free(radar_scans[i].box);

    return 0;
}



