// This file tests the command centre to see if things work. 
//
//
//


#include <math.h>
#include <stdlib.h>
#include <time.h>
#include <stdlib.h>
#include <time.h>
#include <stdbool.h>
#include <float.h>


#include "common.h"

#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "vertical_profiles.h"
#include "radars.h"
#include "processing.h"
#include "control_centre.h"

int main() {

    //clock_t start = clock();
   double sim_time = 60.0; 
   int max_vol_scans = (int)((330.0-sim_time)/5);
//   int max_vol_scans = (int)((20.0-sim_time)/5);
   // Example: generate 3 command files automatically
    for (int i = 0; i < max_vol_scans; i++) {
        generate_commands_file(i, sim_time);
	sim_time += 5.0;
    }


	// Setting up rainfall
    // Create raincell and spatial_raincell
    Raincell* raincell = create_raincell(1, 0.5, 15000.0, -0.5);   
   raincell_list[raincell_count] = raincell; 
    Spatial_raincell* s_raincell = create_spatial_raincell(1, -80000.0,80000.0,10);
	
   s_raincell_list[raincell_count++] = s_raincell; 


// defining VPR:
//
VPR_params *params = malloc(sizeof(VPR_params));
init_VPR_params(params);

      fill_VPR_params(params,
        60.0*60, 120.0*60.0, 170.0*60.0, 200.0*60.0, 230.0*60.0,
        7.0, //8000.0,
	     2000.0, 3000.0,        // Echo top
        45.0, 1.0, 1.0, 2.0,         // Bright band Z
        3000.0, 100.0, 50.0,       // Bright band heights
        15.0, 2.0, 1.0,              // Width Z
        750.0, 500.0, 250.0,       // Width H
        0.65,-0.4, -0.15,-0.1,           // Ratio
        35, -3.0, 2.0, 14.0,         // Cell base Z
        500.0, 150.0, 25.0,           // Cell base heights
	0.0005			     // gradient in dB /m.... 
    );


VPR *VPR_strat   = create_and_fill_VPR(params);
    VPR *VPR_conv  = create_VPR();

    VPR *VPR_A_clima =create_VPR();
    VPR *VPR_A_gmd  =create_VPR();
  

    VPR *VPR_A_d = create_VPR();

    VPR *VPR_dummy = create_VPR();
    
    double t1,t2, t3;// timeB;
    t1 = params->t_growth_start;
    t2 = params->t_decay_end;
    t3 = params->t_mature_end;
 
compute_climatology_VPR(VPR_A_clima,params,60.0,70.0 * 60.0, VPR_dummy); 
compute_average_VPR(VPR_A_gmd, params, t1, t2, 60.0, VPR_dummy);
compute_average_VPR(VPR_A_d,   params, t3, t2, 60.0, VPR_dummy);






	// Create radar list
    Radar* radar1 = create_radar(1, "C", "PPI", 0.0, 0.0, 100.0, 250000.0, 250.0, 1.0);
    Radar* radar2 = create_radar(2, "X", "PPI", -50000.0, 50000.0, 25.0, 50000.0, 100.0, 0.5);
// Assuming radar_count starts at 0
radar_list[radar_count++] = radar1;  // Add radar1 to the list
radar_list[radar_count++] = radar2;  // Add radar2 to the list


//	Radar* radar_test = radar1;


    // Start monitoring inputs (reads files once and archives them)
    monitor_and_process_inputs(VPR_strat,params, VPR_conv);

    return 0;
}
