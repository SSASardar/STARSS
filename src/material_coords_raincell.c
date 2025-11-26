/**
 * @file material_coords_raincell.c
 *
 * @brief The functions of the material/lagrangian description of the raincell.
 *
 */





// include statements: 
#include "material_coords_raincell.h"
#include "common.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>


//global registries:
/**
 * @brief List of pointers to all raincell objects in the system.
 *
 * This global array holds pointers to `Raincell` structures.
 * The maximum number of raincells is defined by `MAX_RAINCELLS`.
 * Actual number of raincells is tracked by `raincell_count`.
 */
Raincell* raincell_list[MAX_RAINCELLS];

/**
 * @brief Number of raincells currently stored in `raincell_list`.
 *
 * This is incremented as raincells are added and used to keep track
 * of the number of active entries in the `raincell_list` array.
 */
int raincell_count = 0;



Raincell* create_raincell(int id, double relative_size_core, double radius_stratiform, double relative_offset) {

	Raincell* raincell = malloc(sizeof(Raincell));
	raincell->id =  id;
	raincell->radius_core = relative_size_core*radius_stratiform;
	raincell->radius_stratiform = radius_stratiform;
	raincell->offset_centre_core = relative_offset*radius_stratiform;
	return raincell;

}



void print_raincell(const Raincell* raincell){

printf("\n\nRaincell %d: \n 	Centre: 	(0,0)\n 	Radius:		%.2lf\n ", raincell->id, raincell->radius_stratiform);
printf("\nIts core has: \n 	Centre: 	(%.2lf, %.2lf)\n 	Radius: 	%.2lf\n", raincell->offset_centre_core, 0.00, raincell->radius_core);
}



void free_raincell(Raincell* raincell){
	free(raincell);
}


// Uses the global raincell_list and raincell_count
const Raincell* find_raincell_by_id_ONLY(int idA) {
    for (int i = 0; i <raincell_count; ++i) {
        if (raincell_list[i]->id == idA) {
            return raincell_list[i];  // Found
        }
    }
    printf("find_raincell_by_id_ONLY()\nRaincell with id %d was not found. Returning NULL\n\n", idA);
    return NULL; // Not found
}

