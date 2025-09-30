/**
 * @file spatial_coords_raincell.h
 * @brief structures and functions for spatial/eulerian description of raincell
 */




#ifndef SPATIAL_COORDS_RAINCELL_H
#define SPATIAL_COORDS_RAINCELL_H

#include "common.h"
#include "material_coords_raincell.h"


/**
 * @struct Spatial_raincell
 * @brief Holds the unique identifier, the initial positions and the velocity split in components
 */
typedef struct Spatial_raincell {
	int id;
	double initial_x;
	double initial_y;
	double dx;
	double dy;
} Spatial_raincell;



//global registries:
/**
 * @brief Global list of spatial raincells for easy access
 */
extern Spatial_raincell* s_raincell_list[MAX_RAINCELLS];





/**
 * @brief setting the initial positions and the velocity of a specific raincell.
 * 
 * Now all the volecity goes to the x component.
 */
Spatial_raincell* create_spatial_raincell(int d, double intial_x, double intial_y, double velocity);

/**
 * @brief retrieving a Spatial_raincell from the global list using its id.
 */
const Spatial_raincell* find_spatial_raincell_by_id_ONLY(int idA);

/**
 * @brief [DEBUG] printing the path of the raincell through the simulation domain in Cartesian coordinates.
 */
void print_path_spatial_raincell(const Spatial_raincell* s_raincell);

/**
 * @brief Freeing memory
 */
void free_spatial_raincell(Spatial_raincell* s_raincell);

Point* get_position_raincell(double time, const Spatial_raincell* cell);

Bounding_box* create_BoundingBox_for_s_raincell(const Spatial_raincell* s_raincell, double time,  const Raincell* raincell);





#endif /* SPATIAL_COORDS_RAINCELL_H*/


