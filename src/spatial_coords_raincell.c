// THis is a .c file containing the spatial coordinate descriptions of the raincell. 






// include statements
#include "spatial_coords_raincell.h"
#include "material_coords_raincell.h"
#include "common.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>





Spatial_raincell* s_raincell_list[MAX_RAINCELLS];

Spatial_raincell* create_spatial_raincell(int id, double initial_x, double initial_y, double velocity) {
	Spatial_raincell* s_raincell = malloc(sizeof(Spatial_raincell));
	s_raincell->id = id;
	s_raincell->initial_x = initial_x;
	s_raincell->initial_y = initial_y;
	s_raincell->dx = velocity;
	s_raincell->dy = 0;

//	printf("I just crafted spatial raincell %d\n\n", s_raincell->id);

	return s_raincell;	
}

// Function to find Spatial_raincell by ID ONLY
const Spatial_raincell* find_spatial_raincell_by_id_ONLY(int idA) {
    for (int i = 0; i < raincell_count; ++i) {
        if (s_raincell_list[i]->id == idA) {
            return s_raincell_list[i];  // Found
        }
    }
    printf("find_spatial_raincell_by_id_ONLY()\nSpatial_raincell with id %d was not found. Returning NULL\n\n", idA);
    return NULL; // Not found
}





void print_path_spatial_raincell(const Spatial_raincell* s_raincell){
	printf("Spatial raincell %d:\n 		The parametric equations for the path centre of cell (x(t), y(t)) is:\n 		x(t) = %.2lf * t + %.2lf\n		y(t) = %.2lf * t + %.2lf\n\n", s_raincell->id, s_raincell->dx, s_raincell->initial_x, s_raincell->dy, s_raincell->initial_y);

}

void free_spatial_raincell(Spatial_raincell* s_raincell){
	free(s_raincell);
}

Point* get_position_raincell(double time, const Spatial_raincell* cell) {
    if (!cell) {
        fprintf(stderr, "get_position_raincell: NULL cell provided\n");
        return NULL;
    }

    Point* point = malloc(sizeof(Point));
    if (!point) {
        perror("malloc failed in get_position_raincell");
        return NULL;
    }

    point->x = cell->initial_x + time * cell->dx;
    point->y = cell->initial_y + time * cell->dy;

    return point;
}

Bounding_box* create_BoundingBox_for_s_raincell(const Spatial_raincell* s_raincell, double time, const Raincell* raincell){
	Bounding_box* bounding_box = malloc(sizeof(Bounding_box));
	double radius_stratiform = raincell->radius_stratiform;
	Point* centre = get_position_raincell(time, s_raincell);
	    // Build corners based on center and radius (assuming square bounding box)
    bounding_box->topLeft.x = centre->x - radius_stratiform;
    bounding_box->topLeft.y = centre->y + radius_stratiform;

    bounding_box->topRight.x = centre->x + radius_stratiform;
    bounding_box->topRight.y = centre->y + radius_stratiform;

    bounding_box->bottomLeft.x = centre->x - radius_stratiform;
    bounding_box->bottomLeft.y = centre->y - radius_stratiform;

    bounding_box->bottomRight.x = centre->x + radius_stratiform;
    bounding_box->bottomRight.y = centre->y - radius_stratiform;

    // Clean up the allocated center point if you don't need it anymore
    free(centre);


    return bounding_box;
}
