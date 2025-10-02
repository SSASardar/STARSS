/**
 * @file material_coords_raincell.h
 *
 * @brief Structures and functions involved with the material/lagrangian description of the raincell.
 *
 */


#ifndef MATERIAL_COORDS_RAINCELL_H
#define MATERIAL_COORDS_RAINCELL_H

#define MAX_RAINCELLS 2

/**
 * @struct Raincell
 * @brief Once circle of stratiform rain, with within it a smaller circle of convective rain
 *
 */
typedef struct Raincell {

	int id;/**< raincell unique identifyer*/
	double radius_core;/**< the radius of the smaller convective rain core*/
	double radius_stratiform;/**< the radius of the larger stratiform rain*/
	double offset_centre_core;/**< where the centre of the core is relative to the centre of the larger circle*/
} Raincell;

	
Raincell* create_raincell(int id, double relative_size_core, double radius_stratiform, double relative_offset);


//global registries:

extern Raincell* raincell_list[MAX_RAINCELLS];
extern int raincell_count;





/**
 * @brief [DEBUG] printing the location of the centre and the core of the raincell.
 */
void print_raincell(const Raincell* raincell);

/**
 * @brief freeing raincell structures
 */
void free_raincell(Raincell* raincell);

/**
 * @brief retrieving the raincell with a certain unique identifier (id)
 */
const Raincell* find_raincell_by_id_ONLY(int idA);




#endif /* MATERIAL_COORDS_RAINCELL_H */
