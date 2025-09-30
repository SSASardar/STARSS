#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "radars.h"
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "common.h"

int main() {
    // Create radar list
    Radar* radar1 = create_radar(1, "C", "PPI", 0.0, 0.0, 100.0, 250000.0, 100.0, 1.0);
    Radar* radar2 = create_radar(2, "X", "PPI", -50000.0, 50000.0, 60.0, 50000.0, 50.0, 1.0);

const Radar* radars[] = { radar1, radar2 };
    int num_radars = sizeof(radars) / sizeof(radars[0]);

    // Create raincell and spatial_raincell
    Raincell* raincell = create_raincell(1, 0.5, 10000.0, -0.5);   
    
    Spatial_raincell* s_raincell = create_spatial_raincell(1, -120000.0,80000.0, 6);
	
	Radar* radar_test = radar1;

    //double time = 210.00*60;
    double time;
    Polar_box* box = init_polar_box();
    
    for (int ti = 0; ti<16;ti++){
    	  // time = (265.0+(double)ti*(0.3125))*60.0;
    	   time = (200.0+(double)ti*(0.3125));
      	double time_in_sec = time*60.0;
	   Bounding_box* true_box = create_BoundingBox_for_s_raincell(s_raincell, time_in_sec, raincell);


	// update the elevation angle: 
	if (ti<8){
		update_other_angle(box, (double)ti*2.0*DEG2RAD);
	} else {
		update_other_angle(box, ((double)ti-8.0)*2*DEG2RAD);
	}



	// Fill polar box
	    if (fill_polar_box(box, time_in_sec, s_raincell, radar_test, raincell) != 0) {
        printf("Failed to update polar box for iteration %d\n", ti);
        // handle error if needed
    }


    Bounding_box* bounded_polar_box = create_bounding_box_for_polar_box(box, radars, num_radars);

print_bounding_box(bounded_polar_box);

    // Find radar associated with polar box
    const  Radar* found_radar = find_radar_by_id(box, radars, num_radars);
    if (found_radar) {
        printf("Radar found: ID = %d, Frequency = %s, Max Range = %.2f\n",
               get_radar_id(found_radar), get_frequency(found_radar), get_max_range_radar(found_radar));
    } else {
        printf("Radar not found.\n");
    }


fill_polar_box_grid(box, radar_test, s_raincell, raincell, time_in_sec);

save_polar_box_grid_to_file(box, radar_test, ti, time, "outputs/radar_scans.txt");
}
printf("===================\n\n");
// Cleanup
       free_spatial_raincell(s_raincell);
         free_raincell(raincell);

    
    free(radar1);
    free(radar2);
    free(box);

    return 0;










}
