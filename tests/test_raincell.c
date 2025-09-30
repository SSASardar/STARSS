#include <stdio.h>
#include <math.h>
#include "material_coords_raincell.h"
//#include "true_vertical_profile.h"
//#include "spatial_coords_raincell.h"

int main(void) {
    printf("Programme started.\n");

    // Create a material raincell
    Raincell* raincell = create_raincell(1,0.3, 15000.0,-0.5);
    
print_raincell(raincell);

	printf("Freeing memory:\n");
	free_raincell(raincell);
    printf("Programme finished.\n");
    return 0;
}
