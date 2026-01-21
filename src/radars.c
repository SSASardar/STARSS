// This is the radar.c file
// 	It defines the structure of a radar
// 	It can execute scanning instructions



// include statements:
#include "radars.h"
#include "spatial_coords_raincell.h"
#include "material_coords_raincell.h"
#include "common.h"
#include "vertical_profiles.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <ctype.h>
#include <assert.h>
#include <errno.h>
#include <ctype.h>



// Global registries:
// // Global radar registry to deduplicate
Radar* radar_list[MAX_RADARS];
int radar_count = 0;

// Scan collection
RadarScan radar_scans[MAX_SCANS];//ONLY STORE ONE SCAN!! PLEASE! 
int scan_count = 0;


//Creating a radar
Radar* create_radar(int id, const char* frequency, const char* scanning_mode,
                    double x, double y, double z,  double max_range,
                    double range_res, double angular_res) {
    Radar* r = (Radar*)malloc(sizeof(Radar));
    if (r == NULL) {
        printf("Memory allocation failed.\n");
        return NULL;
    }

    r->id = id;
    strncpy(r->frequency, frequency, 1);
    r->frequency[1] = '\0';

    strncpy(r->scanning_mode, scanning_mode, 3);
    r->scanning_mode[3] = '\0';

    r->x = x;
    r->y = y;
    r->z = z;
    r->maximum_range = max_range;
    r->range_resolution = range_res;
    r->angular_resolution = angular_res;

    return r;
}


Radar* get_or_create_radar(int id, const char* freq, const char* mode,double x, double y, double z, double max_range,double range_res, double angular_res) {
    for (int i = 0; i < radar_count; ++i) {
        if (radar_list[i]->id == id)
            return radar_list[i];
    }

    Radar* r = create_radar(id, freq, mode, x, y, z, max_range, range_res, angular_res);
    if (r && radar_count < MAX_RADARS)
        radar_list[radar_count++] = r;
    return r;
}



// To check the radar setup
void print_radar_specs(const Radar* radar) {
    if (radar == NULL) {
        printf("Radar is not found (pointing to NULL).\n");
        return;
    }

    printf("Radar ID: %d\n", radar->id);
    printf("Frequency: %s\n", radar->frequency);
    printf("Scanning Mode: %s\n", radar->scanning_mode);
    printf("Position (x,y,z): (%.2f, %.2f, %.2lf)\n", radar->x, radar->y, radar->z);  // Removed radar->z since it's not defined
    printf("Max Range: %.2f\n", radar->maximum_range);
    printf("Range Res: %.2f\n", radar->range_resolution);
    printf("Angular Res: %.2f\n", radar->angular_resolution);
}



Point* get_position_radar(const Radar* radar){
	Point* point = malloc(sizeof(Point));
	if (radar) {
		point->x = radar->x;
		point->y = radar->y;
	}	
	return point;
}
double get_height_of_radar(const Radar* radar){
return radar->z;
}
double get_range_res_radar(const Radar* radar){
	return radar->range_resolution;
}

double get_angular_res_radar(const Radar* radar){
	return radar->angular_resolution;
}

int get_radar_id(const Radar* radar){
	return radar->id;
}

double get_max_range_radar(const Radar* radar){
	return radar->maximum_range;
}	


const char* get_frequency(const Radar* r) {
    return r->frequency;
}

const char* get_scanning_mode(const Radar* r) {
    return r->scanning_mode;
}

Polar_box* create_polar_box(
    int radar_id,
    const char* scanning_mode,
    double min_range_gate,
    double max_range_gate,
    double min_angle,
    double max_angle,
    double num_ranges,
    double num_angles,
    double range_res,
    double angular_res,
    int grid_size,
    double other_angle,
    double *grid_data,
    int height_size,
    double *height_data
) {
    Polar_box* box = (Polar_box*)malloc(sizeof(Polar_box));
    if (!box) {
        printf("Memory allocation failed for Polar_box.\n");
        return NULL;
    }

    // Initialize all pointers to NULL
    box->grid = NULL;
    box->attenuation_grid = NULL;
    box->height_grid = NULL;

    // Set scalar values
    box->radar_id = radar_id;
    strcpy(box->scanning_mode,scanning_mode);
    box->min_range_gate = min_range_gate;
    box->max_range_gate = max_range_gate;
    box->min_angle = min_angle;
    box->max_angle = max_angle;
    box->num_ranges = num_ranges;
    box->num_angles = num_angles;
    box->range_resolution = range_res;
    box->angular_resolution = angular_res;
    box->other_angle = other_angle;

    // Allocate grid and attenuation_grid if needed
    if (grid_size > 0 && grid_data != NULL) {
        box->grid = (double*)malloc(sizeof(double) * grid_size);
        box->attenuation_grid = (double*)malloc(sizeof(double) * grid_size);

        if (!box->grid || !box->attenuation_grid) {
            printf("Grid allocation failed.\n");
            free(box->grid);
            free(box->attenuation_grid);
            free(box);
            return NULL;
        }

        memcpy(box->grid, grid_data, sizeof(double) * grid_size);
        memset(box->attenuation_grid, 0, sizeof(double) * grid_size); // initialize to 0
    }

    // Allocate height_grid if needed
    if (height_size > 0 && height_data != NULL) {
        box->height_grid = (double*)malloc(sizeof(double) * height_size);
        if (!box->height_grid) {
            printf("Height grid allocation failed.\n");
            free(box->grid);
            free(box->attenuation_grid);
            free(box);
            return NULL;
        }
        memcpy(box->height_grid, height_data, sizeof(double) * height_size);
    }


    return box;
}



Polar_box* init_polar_box() {
    Polar_box* polar_box = malloc(sizeof(Polar_box));
    if (!polar_box) {
        fprintf(stderr, "Failed to allocate Polar_box\n");
        return NULL;
    }
    // Initialize pointers to NULL or zero out members as needed
    polar_box->grid = NULL;
    polar_box->height_grid = NULL;
    polar_box->attenuation_grid = NULL;
    // Initialize other members to sensible defaults, e.g. 0
    polar_box->range_resolution = 0.0;
    polar_box->angular_resolution = 0.0;
    polar_box->min_range_gate = 0;
    polar_box->max_range_gate = 0;
    polar_box->min_angle = 0;
    polar_box->max_angle = 0;
    polar_box->num_ranges = 0;
    polar_box->num_angles = 0;
    polar_box->radar_id = -1; // or any invalid default
polar_box->other_angle = 0;
strcpy(polar_box->scanning_mode, "");
return polar_box;
}

void update_other_angle(Polar_box* p_box, double new_angle){

	if(p_box == NULL){printf("in radars.c the updating angle failed because of a NULL polar box\n"); return;}

	p_box->other_angle = new_angle;
}
int fill_polar_box(Polar_box* polar_box, double time,
                   const Spatial_raincell* s_raincell,
                   const Radar* radar, const Raincell* raincell, const VPR_params *params) {
    if (!polar_box || !radar || !s_raincell || !raincell) return -1;


        if (strcmp(get_scanning_mode(radar), "PPI") == 0) {
	strcmp(polar_box->scanning_mode,"PPI");
    if (cos(polar_box->other_angle*DEG2RAD) <= 0.0) {
    fprintf(stderr,
            "fill_polar_box: Unsupported elevation angle %.2f rad (cos<=0)\n",
            polar_box->other_angle*DEG2RAD);
    return -1;
}
    double kea_and_radar = KEA + radar->z;

    Point* centre = get_position_raincell(time, s_raincell);//time in seconds.
    Point* radar_point = get_position_radar(radar);

    double diff_x = centre->x - radar_point->x;
    double diff_y = centre->y - radar_point->y;
    double dist_s = sqrt(diff_x * diff_x + diff_y * diff_y);
    double dist = sin(dist_s / kea_and_radar) * kea_and_radar / cos(polar_box->other_angle*DEG2RAD);
    double radius_stratiform = raincell->radius_stratiform;

    polar_box->range_resolution = get_range_res_radar(radar);
    polar_box->angular_resolution = get_angular_res_radar(radar);

    double angle = atan2(diff_y, diff_x);
    if (angle < 0) angle += 2 * M_PI;
    angle = angle * RAD2DEG;

    double del_angle = atan2(radius_stratiform, dist) * RAD2DEG;

    polar_box->radar_id = get_radar_id(radar);

    // Compute min/max gates and angles
    polar_box->min_range_gate = floor((sin((fabs(dist_s - radius_stratiform))/kea_and_radar)*kea_and_radar/cos(polar_box->other_angle*DEG2RAD)) / polar_box->range_resolution);
    polar_box->max_range_gate = ceil((sin((fabs(dist_s + radius_stratiform))/kea_and_radar)*kea_and_radar/cos(polar_box->other_angle*DEG2RAD)) / polar_box->range_resolution);

if (polar_box->min_range_gate > polar_box->max_range_gate) {
    int tmp = polar_box->min_range_gate;
    polar_box->min_range_gate = polar_box->max_range_gate;
    polar_box->max_range_gate = tmp;
}

double padding_angle = 2.0;
    polar_box->min_angle = floor((angle - del_angle-padding_angle)/polar_box->angular_resolution);
    polar_box->max_angle = ceil((angle + del_angle+padding_angle)/polar_box->angular_resolution);

    // Dynamically compute sizes
    int num_ranges = (int)lround(polar_box->max_range_gate - polar_box->min_range_gate + 1);
double span = polar_box->max_angle - polar_box->min_angle;
if (span < 0) span += 360.0;
int num_angles = (int)ceil(span);
    //
 //int num_angles = (int)lround((polar_box->max_angle - polar_box->min_angle + 1 + 2*padding_angle_deg)/ polar_box->angular_resolution);

    // Only reallocate if size changed or not allocated yet
    if (!polar_box->grid || (int)polar_box->num_ranges != num_ranges || (int)polar_box->num_angles != num_angles) {
        free(polar_box->grid);
        free(polar_box->height_grid);
	free(polar_box->attenuation_grid);

        polar_box->grid = malloc(sizeof(double) * num_ranges * num_angles);
        polar_box->height_grid = malloc(sizeof(double) * num_ranges * num_angles);
    	polar_box->attenuation_grid = malloc(sizeof(double) * num_ranges * num_angles);
    	if (!polar_box->grid || !polar_box->height_grid || !polar_box->attenuation_grid) {
            perror("Failed to allocate polar box grids");
            free(centre);
            free(radar_point);
            return -1;
        }
    }

    polar_box->num_ranges = num_ranges;
    polar_box->num_angles = num_angles;
    


    free(centre);
    free(radar_point);
    }



    if (strcmp(get_scanning_mode(radar), "RHI") == 0) {

	strcmp(polar_box->scanning_mode,"RHI");
   // double kea_and_radar = KEA + radar->z;

    Point* centre = get_position_raincell(time, s_raincell);//time in seconds.
    Point* radar_point = get_position_radar(radar);

   //double offset_core_in_absolute = raincell->offset_centre_core * raincell->radius_stratiform;
    //double diff_x = centre->x + offset_core_in_absolute - radar_point->x; 
    
    double diff_x = centre->x - raincell->offset_centre_core - radar_point->x;
    
    double diff_y = centre->y - radar_point->y;
    //double dist_s = sqrt(diff_x * diff_x + diff_y * diff_y);
  //  double dist = sin(dist_s / kea_and_radar) * kea_and_radar / cos(polar_box->other_angle*DEG2RAD);
    //double radius_stratiform = raincell->radius_stratiform;

    polar_box->range_resolution = get_range_res_radar(radar);
    polar_box->angular_resolution = get_angular_res_radar(radar);

    double other_angle = atan2(diff_y, diff_x);
   //double other_angle = atan2(diff_x, diff_y);
    //if (other_angle < 0) other_angle += 2 * M_PI;

    polar_box->other_angle = other_angle * RAD2DEG;

/*
 FILE *debug = fopen("outputs/aDEBUG.txt", "a");
 fprintf(debug, "%.2lf, %.2lf, %.2lf, %.2lf, %.2lf, %.2lf, %.2lf, %.2lf, %.2lf\n", time, radar_point->x, radar_point->y, centre->x, centre->y, diff_x, diff_y, other_angle, polar_box->other_angle);
fclose(debug);
*/


    double m = diff_y/diff_x;
double c = radar_point->y - m * radar_point->x;

//double A = 1 + (m * m);
//double B = -2*centre->x + 2 * radar_point->y * m - 2 * centre->x * m * m - 2 * centre->y * m;
//double C = centre->x * centre->x + radar_point->y * radar_point->y - 2 * radar_point->x * radar_point->y * m + radar_point->x * radar_point->x * m * m - 2 * radar_point->y * centre->y + 2 * radar_point->x * centre->y * m + centre->y * centre->y -  raincell->radius_stratiform * raincell->radius_stratiform;

double A = 1 + (m*m);
double B = (-2*centre->x + 2 * c * m - 2 * m * centre->y);
double C = (centre->x * centre->x) + (c*c) - (2 * c * centre->y) + (centre->y * centre->y) - (raincell->radius_stratiform * raincell->radius_stratiform);

double x_1 = (-B + sqrt(B * B - 4 * A * C))/ (2 * A);
double x_2 = (-B - sqrt(B * B - 4 * A * C))/ (2 * A);

//double y_1 = sqrt(raincell->radius_stratiform - (x_1 - centre->x) * (x_1 - centre->x)) + centre->y;
//double y_2 = sqrt(raincell->radius_stratiform - (x_2 - centre->x) * (x_2 - centre->x)) + centre->y;
double y_1 = m*x_1+c;
double y_2 = m*x_2+c;
/*
double x_rmin, x_rmax, y_rmin, y_rmax;

//    FILE *fpz = fopen("outputs/quads.txt", "a");   // open file for writing
//    if (!fpz) {
//        perror("fopen");
//        return 1;
//    }

  //  fprintf(fpz, "%.2e, %.2e, %.2e  ||  %.2e, %.2e || x_1 = %.2e, x_2 = %.2e || y_1 = %.2e, y_2 = %.2e\n", A,B,C, B*B-(4*A*C), sqrt( B*B-(4*A*C)), x_1, x_2, y_1, y_2);

    //fclose(fpz);

//double checking_angle = fmod(polar_box->other_angle,360);
//if(checking_angle>270 && checking_angle<=90){x_rmin = x_2; x_rmax = x_1; y_rmin = y_2; y_rmax = y_1;} else {x_rmin = x_1; x_rmax = x_2; y_rmin = y_1; y_rmax = y_2;}
if(fabs(x_1)>fabs(x_2)){x_rmin = x_2;x_rmax = x_1;} else {x_rmin = x_1; x_rmax = x_2;}
//if((x_1)<(x_2)){x_min = x_2;x_max = x_1;} else {x_min = x_1; x_max = x_2;}

//if(fabs(y_1)>fabs(y_2)){y_rmin = y_2;y_rmax = y_1;} else {y_rmin = y_1; y_rmax = y_2;}
//if((y_1)<(y_2)){y_min = y_2;y_max = y_1;} else {y_min = y_1; y_max = y_2;}

y_rmin = x_rmin*m + c;
y_rmax = x_rmax*m + c;

*/


double r_min, r_a, r_max;

/*
r_min = sqrt((x_rmin - radar_point->x)*(x_rmin - radar_point->x) + (y_rmin - radar_point->y)*(y_rmin - radar_point->y));

r_a = sqrt((x_rmax - radar_point->x)*(x_rmax - radar_point->x) + (y_rmax - radar_point->y)*(y_rmax - radar_point->y));

r_max = r_a + params->h_et_0;

//r_min = 0.0;
//r_max = radar->maximum_range;
*/

double r1, r2;

r1 = hypot(x_1 - radar_point->x, y_1 - radar_point->y);
r2 = hypot(x_2 - radar_point->x, y_2 - radar_point->y);
r_min = fmin(r1, r2);
r_max = fmax(r1, r2) + params->h_et_0;



//printf("min and max ranges are %.2lf, %.2lf\n", r_min, r_max);

    polar_box->radar_id = get_radar_id(radar);

    // Compute min/max gates and angles
    polar_box->min_range_gate = floor(r_min / polar_box->range_resolution);
    polar_box->max_range_gate = ceil(r_max / polar_box->range_resolution);

if (polar_box->min_range_gate > polar_box->max_range_gate) {
    int tmp = polar_box->min_range_gate;
    polar_box->min_range_gate = polar_box->max_range_gate;
    polar_box->max_range_gate = tmp;
}

//double padding_angle = 2.0;
    double a_1 = 0;
    double a_2 = atan2(params->h_cb_0, r_min);
    double a_3 = atan2(params->h_et_0, r_min);
    double a_4 = atan2(params->h_et_0, r_min);

    if(a_1<a_2){ polar_box->min_angle = floor(a_1*RAD2DEG/polar_box->angular_resolution);} else { polar_box->min_angle = floor(a_2*RAD2DEG/polar_box->angular_resolution);}
    if(a_3<a_4){polar_box->max_angle = ceil(a_4*RAD2DEG/polar_box->angular_resolution);} else { polar_box->max_angle = ceil(a_3*RAD2DEG/polar_box->angular_resolution);}

if(polar_box->max_angle * polar_box->angular_resolution > 90) polar_box->max_angle = 90/polar_box->angular_resolution;

//printf("minimum angles... %.2lf, %.2lf\n", a_1*RAD2DEG/polar_box->angular_resolution, a_2*RAD2DEG/polar_box->angular_resolution);
    // Dynamically compute sizes
    int num_ranges = (int)lround(polar_box->max_range_gate - polar_box->min_range_gate + 1);
double span = polar_box->max_angle - polar_box->min_angle;
if (span < 0) span += 360.0;
int num_angles = (int)ceil(span);
    //

    // Only reallocate if size changed or not allocated yet
    if (!polar_box->grid || (int)polar_box->num_ranges != num_ranges || (int)polar_box->num_angles != num_angles) {
        free(polar_box->grid);
        free(polar_box->height_grid);
	free(polar_box->attenuation_grid);

        polar_box->grid = malloc(sizeof(double) * num_ranges * num_angles);
        polar_box->height_grid = malloc(sizeof(double) * num_ranges * num_angles);
    	polar_box->attenuation_grid = malloc(sizeof(double) * num_ranges * num_angles);
    	if (!polar_box->grid || !polar_box->height_grid || !polar_box->attenuation_grid) {
            perror("Failed to allocate polar box grids");
            free(centre);
            free(radar_point);
            return -1;
        }
    }

    polar_box->num_ranges = num_ranges;
    polar_box->num_angles = num_angles;
    


    free(centre);
    free(radar_point);
    }

return 0;
}
int get_radar_id_for_polar_box(const struct Polar_box* box) {
    return box->radar_id;
}

double get_min_range_gate(const struct Polar_box* box) {
    return box->min_range_gate;
}

double get_max_range_gate(const struct Polar_box* box) {
    return box->max_range_gate;
}

double get_min_angle(const struct Polar_box* box) {
    return box->min_angle;
}

double get_max_angle(const struct Polar_box* box) {
    return box->max_angle;
}

double get_num_ranges(const struct Polar_box* box) {
    return box->num_ranges;
}

double get_num_angles(const struct Polar_box* box) {
    return box->num_angles;
}

double get_range_res_polar_box(const struct Polar_box* box) {
	return box->range_resolution;
}

double get_angular_res_polar_box(const struct Polar_box* box){
	return box->angular_resolution;
}
	
	// Function to find Radar by ID              
const Radar* find_radar_by_id(const Polar_box* box, const Radar** radars, int num_radars) {
    for (int i = 0; i < num_radars; ++i) {   
        if (radars[i]->id == get_radar_id_for_polar_box(box)) {
            return radars[i];
        }
    }
    printf("find_radar_by_id()\nRadar with id %d was not found. found_radar is allocated to NULL\n\n", get_radar_id_for_polar_box(box));
    return NULL; // Not found

}

	// Function to find Radar by ID ONLY BY ID!!              
const Radar* find_radar_by_id_ONLY(int idA) {
    for (int i = 0; i < radar_count; ++i) {   
        if (radar_list[i]->id == idA) {
            return radar_list[i];
        }
    }
    printf("find_radar_by_id_ONLY()\nRadar with id %d was not found. found_radar is allocated to NULL\n\n", idA);
    return NULL; // Not found

}



void print_polar_box(const Polar_box* box) {
    if (box == NULL) {
        printf("polar box not found (points to NULL) in print_polar_grid function.\n\n");
        return;
    }

    // Print polar box info directly from the box
    printf("Radar ID      : %d\n", box->radar_id);
    printf("Num of Angles : %.0d\n", box->num_angles);
    printf("Num of Ranges : %.0d\n", box->num_ranges);
    printf("Between angles: [%.2f, %.2f]\n", box->min_angle, box->max_angle);
    printf("Between ranges: [%.2f, %.2f]\n",
           box->min_range_gate * box->range_resolution,
           box->max_range_gate * box->range_resolution);

	printf("the four values: {%.2lf,\n 	%.2lf,\n	%.2lf,\n	%.2lf}\n\n\n", box->min_range_gate * box->range_resolution*cos(box->min_angle*DEG2RAD),box->min_range_gate * box->range_resolution*sin(box->min_angle*DEG2RAD),box->max_range_gate * box->range_resolution*cos(box->min_angle*DEG2RAD),box->max_range_gate * box->range_resolution*sin(box->min_angle*DEG2RAD));


    printf("\n");
}


Bounding_box* create_bounding_box_for_polar_box(const Polar_box* p_box, const Radar** radars, int num_radars){
if(p_box==NULL){printf("create_bounding+box_for_polar_plot\n You are trying to create a bounding box for a polar box which is not defined (points to NULL)\n The bounding box will be assigned NULL\n\n");return NULL;}
	
Bounding_box* bbox = malloc(sizeof(Bounding_box));
	const Radar* found_radar = find_radar_by_id(p_box, radars, num_radars);

	if(strcmp(get_scanning_mode(found_radar), "PPI")==0){
double rmin = get_min_range_gate(p_box) * get_range_res_radar(found_radar);
double curvature_correction_min = cos(p_box->other_angle*DEG2RAD + atan2(rmin*cos(p_box->other_angle*DEG2RAD),(KEA+rmin*sin(p_box->other_angle*DEG2RAD))));
double rmax = get_max_range_gate(p_box) * get_range_res_radar(found_radar);
double curvature_correction_max = cos(p_box->other_angle*DEG2RAD + atan2(rmax*cos(p_box->other_angle*DEG2RAD),(KEA+rmax*sin(p_box->other_angle*DEG2RAD))));
double anglemin = get_min_angle(p_box) * DEG2RAD;
double anglemax = get_max_angle(p_box) * DEG2RAD;
double anglemid = (anglemin + anglemax) / 2;

double xs[5] = {
    rmax * curvature_correction_max * cos(anglemin),
    rmin * curvature_correction_min * cos(anglemin),
    rmax * curvature_correction_max * cos(anglemax),
    rmin * curvature_correction_min * cos(anglemax),
    rmax * curvature_correction_max * cos(anglemid)
};

double ys[5] = {
    rmax * curvature_correction_max * sin(anglemin),
    rmin * curvature_correction_min * sin(anglemin),
    rmax * curvature_correction_max * sin(anglemax),
    rmin * curvature_correction_min * sin(anglemax),
    rmax * curvature_correction_max * sin(anglemid)
};


double xmin = xs[0], xmax = xs[0];
double ymin = ys[0], ymax = ys[0];

for (int i = 1; i < 5; ++i) {
    if (xs[i] < xmin) xmin = xs[i];
    if (xs[i] > xmax) xmax = xs[i];
    if (ys[i] < ymin) ymin = ys[i];
    if (ys[i] > ymax) ymax = ys[i];
}

Point* pos_radar = get_position_radar(found_radar);


// Allocate and fill the bounding box
bbox->topLeft.x = xmin+pos_radar->x;
bbox->topLeft.y = ymax+pos_radar->y;

bbox->topRight.x = xmax+pos_radar->x;
bbox->topRight.y = ymax+pos_radar->y;

bbox->bottomLeft.x = xmin+pos_radar->x;
bbox->bottomLeft.y = ymin+pos_radar->y;

bbox->bottomRight.x = xmax+pos_radar->x;
bbox->bottomRight.y = ymin+pos_radar->y;
}

if(strcmp(get_scanning_mode(found_radar), "RHI") == 0){
	double rmin = get_min_range_gate(p_box) * get_range_res_radar(found_radar);
	double rmax = get_max_range_gate(p_box) * get_range_res_radar(found_radar);
	double angleMin = get_min_angle(p_box) * DEG2RAD * get_angular_res_polar_box(p_box);
	double angleMax = get_max_angle(p_box) * DEG2RAD * get_angular_res_polar_box(p_box);
	
	double h_min = calculate_height_of_beam_at_range(rmin, angleMin, found_radar->z);
	double h_max = calculate_height_of_beam_at_range(rmax, angleMax, found_radar->z);
	double h_mid = calculate_height_of_beam_at_range(rmin, angleMax, found_radar->z);
	double h_midd = calculate_height_of_beam_at_range(rmax, angleMin, found_radar->z);

	double smin = KEA*asin((rmin*cos(angleMax))/(KEA+h_mid));
	double smax = KEA*asin((rmax*cos(angleMin))/(KEA+h_midd));

	double radar_dist_from_origin = sqrt(found_radar->x * found_radar->x + found_radar->y * found_radar->y);

	bbox->topLeft.x = radar_dist_from_origin + smin;
	bbox->topLeft.y /*height or z coord */ = h_max;
	
	bbox->topRight.x = radar_dist_from_origin + smax;
	bbox->topRight.y /* height or z coord */= h_max;

	bbox->bottomLeft.x = radar_dist_from_origin + smin;
	bbox->bottomLeft.y /* height or z coord */ = h_min;

	bbox->bottomRight.x = radar_dist_from_origin + smax;
	bbox->bottomRight.y /* height or z coord */ = h_min;
}
return bbox;
}

/*
Bounding_box* create_bounding_box_for_polar_box_EZ(const Polar_box* p_box) {
    if (p_box == NULL) {
        printf("create_bounding_box_for_polar_box_GLOBAL()\n"
               "You are trying to create a bounding box for a polar box which is not defined (points to NULL).\n"
               "The bounding box will be assigned NULL.\n\n");
        return NULL;
    }

    // Use global radar registry
    const Radar* found_radar = find_radar_by_id_ONLY(p_box->radar_id);
    if (found_radar == NULL) {
        printf("create_bounding_box_for_polar_box_GLOBAL()\n"
               "No radar found with id %d. Returning NULL.\n\n", p_box->radar_id);
        return NULL;
    }

    double rmin = get_min_range_gate(p_box) * get_range_res_radar(found_radar);
    double curvature_correction_min = cos(
        p_box->other_angle*DEG2RAD + atan2(rmin * cos(p_box->other_angle*DEG2RAD),
                                   (KEA + rmin * sin(p_box->other_angle*DEG2RAD)))
    );

    double rmax = get_max_range_gate(p_box) * get_range_res_radar(found_radar);
    double curvature_correction_max = cos(
        p_box->other_angle*DEG2RAD + atan2(rmax * cos(p_box->other_angle*DEG2RAD),
                                   (KEA + rmax * sin(p_box->other_angle*DEG2RAD)))
    );

    double anglemin = get_min_angle(p_box) * DEG2RAD;
    double anglemax = get_max_angle(p_box) * DEG2RAD;
    double anglemid = (anglemin + anglemax) / 2;

    double xs[5] = {
        rmax * curvature_correction_max * cos(anglemin),
        rmin * curvature_correction_min * cos(anglemin),
        rmax * curvature_correction_max * cos(anglemax),
        rmin * curvature_correction_min * cos(anglemax),
        rmax * curvature_correction_max * cos(anglemid)
    };

    double ys[5] = {
        rmax * curvature_correction_max * sin(anglemin),
        rmin * curvature_correction_min * sin(anglemin),
        rmax * curvature_correction_max * sin(anglemax),
        rmin * curvature_correction_min * sin(anglemax),
        rmax * curvature_correction_max * sin(anglemid)
    };

    double xmin = xs[0], xmax = xs[0];
    double ymin = ys[0], ymax = ys[0];

    for (int i = 1; i < 5; ++i) {
        if (xs[i] < xmin) xmin = xs[i];
        if (xs[i] > xmax) xmax = xs[i];
        if (ys[i] < ymin) ymin = ys[i];
        if (ys[i] > ymax) ymax = ys[i];
    }

    Point* pos_radar = get_position_radar(found_radar);

    // Allocate and fill the bounding box
    Bounding_box* bbox = malloc(sizeof(Bounding_box));
    if (!bbox) {
        printf("Memory allocation failed for Bounding_box.\n");
        return NULL;
    }

    bbox->topLeft.x     = xmin + pos_radar->x;
    bbox->topLeft.y     = ymax + pos_radar->y;
    bbox->topRight.x    = xmax + pos_radar->x;
    bbox->topRight.y    = ymax + pos_radar->y;
    bbox->bottomLeft.x  = xmin + pos_radar->x;
    bbox->bottomLeft.y  = ymin + pos_radar->y;
    bbox->bottomRight.x = xmax + pos_radar->x;
    bbox->bottomRight.y = ymin + pos_radar->y;

    return bbox;
}
*/



double calculate_height_of_beam_at_range(double range, double elevation, double height_of_radar){
	double height_from_earth_centre = (KEA+1.33333333*height_of_radar);
	//double corrected_elevation = elevation*DEG2RAD + atan2(range*cos(elevation*DEG2RAD), KEA+range*sin(elevation*DEG2RAD));
	
	double corrected_elevation = elevation*DEG2RAD;
	// Something is wrong here... is this return equation (4) or equation (5c) in A Comparison of the radar ray path euqations and approximations for use in radar data assimilation, bu Jidong Gao, Keith brewster and Ming Xue. I changed this to equation 4.... so then the corrected elevation angle makes no sense anymore. Just regular elevation angle is fine. 
	return sqrt(range*range + height_from_earth_centre*height_from_earth_centre + 2*range*height_from_earth_centre*sin(corrected_elevation))-height_from_earth_centre;
}


int sample_from_relative_location_in_raincell(double range, double angle, double elevation, const Point* radar_centre, const Point* spatial_centre, const Raincell* raincell) {

	
    double curvature_correction = cos(elevation*DEG2RAD + atan2(range*cos(elevation*DEG2RAD),(KEA+range*sin(elevation*DEG2RAD))));
    // 1. Convert polar to cartesian in radar coordinates
    double dx = range * curvature_correction * cos(angle*DEG2RAD);
    double dy = range * curvature_correction * sin(angle*DEG2RAD);

    // 2. Absolute coordinates of the radar sample point
    double sample_x = radar_centre->x + dx;
    double sample_y = radar_centre->y + dy;

    // 3. Compute coordinates relative to raincell center
    double rel_x = sample_x - spatial_centre->x;
    double rel_y = sample_y - spatial_centre->y;

    // 4. Apply core offset in the direction of movement (assume offset along x-axis for simplicity)
    double core_centre_x = raincell->offset_centre_core;
    double core_rel_x = rel_x + core_centre_x;

    // 5. Compute distances
    double distance_to_centre = sqrt(rel_x * rel_x + rel_y * rel_y);
    double distance_to_core = sqrt(core_rel_x * core_rel_x + rel_y * rel_y);

    // 6. Determine which region the sample lies in
    if (distance_to_centre > raincell->radius_stratiform) {
        return 0; // Outside the raincell
    } else if (distance_to_core <= raincell->radius_core) {
        return 2; // Inside core region
    } else {
        return 1; // Inside stratiform region
    }
}

void fill_polar_box_grid(Polar_box* box, const Radar* radar,
                         const Spatial_raincell* s_raincell, const Raincell* raincell,
                         double time, const VPR *vpr_strat, const VPR *vpr_conv) {
    if (!box || !radar || !s_raincell || !raincell) return;

    int num_ranges = (int)box->num_ranges;
    int num_angles = (int)box->num_angles;

    // Ensure the struct matches actual allocated sizes
box->num_ranges = num_ranges;
box->num_angles = num_angles;
    Point* pos_radar = get_position_radar(radar);
    Point* pos_raincell = get_position_raincell(time, s_raincell);
    double h0 = get_height_of_radar(radar);

    
    double refl_dBZ = 0.0;
    double att = 0.0;



if(strcmp(get_scanning_mode(radar), "PPI") == 0){
    for (int ri = 0; ri < num_ranges; ri++) {
        double r1 = (box->min_range_gate + ri) * box->range_resolution;
        double sample_height = calculate_height_of_beam_at_range(r1, box->other_angle, h0);

        for (int ai = 0; ai < num_angles; ai++) {
            double a1 = (box->min_angle + ai)*box->angular_resolution;
 int sample = sample_from_relative_location_in_raincell(r1, a1, box->other_angle, pos_radar, pos_raincell, raincell);
int idp = ri * num_angles + ai;
int idp_min_one = idp;
if (ri != 0) {
        idp_min_one = (ri-1) * num_angles + ai;
}


if (sample == 0) { //raincell shape is always convex, so no strange things need to happen.
        box->grid[idp] = 0.0;
        box->attenuation_grid[idp] = 0.0; 
} else if (sample == 1) {
        refl_dBZ = get_reflectivity_at_height(vpr_strat, sample_height);
        att = compute_specific_attenuation(refl_dBZ, radar); 
       // att = 0.01; 
        if(idp == idp_min_one) {
                box->attenuation_grid[idp] = att;
        } else {
                box->attenuation_grid[idp] = att + box->attenuation_grid[idp_min_one];
        }
        box->grid[idp] = add_noise(radar, refl_dBZ-2*box->attenuation_grid[idp]);
} else {
        refl_dBZ = get_reflectivity_at_height(vpr_conv, sample_height);

        att = compute_specific_attenuation(refl_dBZ, radar); 
        //att = 0.02; 
        if(idp == idp_min_one) {
                box->attenuation_grid[idp] = att;
        } else {
                box->attenuation_grid[idp] = att + box->attenuation_grid[idp_min_one];
        }
        box->grid[idp] = add_noise(radar, refl_dBZ-2*box->attenuation_grid[idp]);
}

            // Flattened grid write
            box->height_grid[idp] = sample_height;
        }
    }
}

if(strcmp(get_scanning_mode(radar), "RHI") == 0){
for (int ri = 0; ri <num_ranges;ri++){
	double r1 = (box->min_range_gate+ri)*box->range_resolution;
	double azimuth_angle = box->other_angle;
	for (int ai = 0; ai < num_angles;ai++){
		double a1 = (box->min_angle + ai) * box->angular_resolution;
		double sample_height = calculate_height_of_beam_at_range(r1, a1, h0);
		int sample = sample_from_relative_location_in_raincell(r1,azimuth_angle, a1, pos_radar, pos_raincell, raincell);
		int idp = ri * num_angles + ai;
		int idp_min_one = idp;
		if (ri !=0){
			idp_min_one = (ri-1) * num_angles+ai;
		}	
		if (sample == 0) {
			box->grid[idp] = 0.0;
			//box->grid[idp] = sample;
			box->attenuation_grid[idp] = 0.0;
		} else if (sample == 1) {
        		refl_dBZ = get_reflectivity_at_height(vpr_strat, sample_height);
		        att = compute_specific_attenuation(refl_dBZ, radar);
        		if(idp == idp_min_one) {
               			box->attenuation_grid[idp] = att;
        		} else {
                		box->attenuation_grid[idp] = att + box->attenuation_grid[idp_min_one];
        		}
        		box->grid[idp] = add_noise(radar, refl_dBZ-2*box->attenuation_grid[idp]);
        		//box->grid[idp] = sample;
        		//box->grid[idp] = refl_dBZ;
		} else {
        		refl_dBZ = get_reflectivity_at_height(vpr_conv, sample_height);

        		att = compute_specific_attenuation(refl_dBZ, radar); 
			if(idp == idp_min_one) {
                		box->attenuation_grid[idp] = att;
        		} else {
                		box->attenuation_grid[idp] = att + box->attenuation_grid[idp_min_one];
        		}
        		box->grid[idp] = add_noise(radar, refl_dBZ-2*box->attenuation_grid[idp]);
        		//box->grid[idp] = sample;
        		//box->grid[idp] = refl_dBZ;
		}
		box->height_grid[idp] = sample_height;
	}
}
}
    free(pos_radar);
    free(pos_raincell);
}



void save_polar_box_grid_to_file(const Polar_box* box, const Radar* radar, int scan_index, double scan_time,const char* filename) {
    FILE* fp = fopen(filename, "a");  // Append mode to handle multiple scans
    if (!fp) {
        perror("Failed to open output file");
        exit(EXIT_FAILURE);
    }  
    
    fprintf(fp, "=== BEGIN RADAR_SCAN ===\n");
    fprintf(fp, "scan.index=%d\n", scan_index);
    fprintf(fp,"scan.time=%lf\n", scan_time);
    // Radar metadata
    fprintf(fp, "radar.id=%d\n", radar->id);
    fprintf(fp, "radar.frequency=%s\n", radar->frequency);
    fprintf(fp, "radar.scanning_mode=%s\n", radar->scanning_mode);
    fprintf(fp, "radar.x=%.3f\n", radar->x);
    fprintf(fp, "radar.y=%.3f\n", radar->y);
    fprintf(fp, "radar.z=%.3f\n", radar->z);
    fprintf(fp, "radar.maximum_range=%.3f\n", radar->maximum_range);
    fprintf(fp, "radar.range_resolution=%.3f\n", radar->range_resolution);
    fprintf(fp, "radar.angular_resolution=%.6f\n", radar->angular_resolution);
    
    // Polar box metadata
    fprintf(fp, "box.radar_id=%d\n", box->radar_id);
    fprintf(fp, "box.min_range_gate=%.3f\n", box->min_range_gate);
    fprintf(fp, "box.max_range_gate=%.3f\n", box->max_range_gate);
    fprintf(fp, "box.min_angle=%.6f\n", box->min_angle);
    fprintf(fp, "box.max_angle=%.6f\n", box->max_angle);
    fprintf(fp, "box.num_ranges=%d\n", box->num_ranges);
    fprintf(fp, "box.num_angles=%d\n", box->num_angles);
    fprintf(fp, "box.range_resolution=%.3f\n", box->range_resolution);
    fprintf(fp, "box.angular_resolution=%.6f\n", box->angular_resolution);
    fprintf(fp, "box.other_angle=%.6f\n", box->other_angle); 
    // Grid data
    int total = (int)(box->num_ranges * box->num_angles);
    fprintf(fp, "grid.size=%d\n", total);
    fprintf(fp, "grid.data=");
    for (int i = 0; i < total; i++) {
        fprintf(fp, "%.2f", box->grid[i]);
        if (i < total - 1) {
            fprintf(fp, " ");
        }
    }
    fprintf(fp, "\n");

    // Height grid data
    if (box->height_grid != NULL) {
        fprintf(fp, "height.size=%d\n", total);
        fprintf(fp, "height.data=");
        for (int i = 0; i < total; i++) {
            fprintf(fp, "%.2f", box->height_grid[i]);
            if (i < total - 1) {
                fprintf(fp, " ");
            }
        }
        fprintf(fp, "\n");
    }

    fprintf(fp, "=== END RADAR_SCAN ===\n\n");

    fclose(fp);
}

/*
 * Read exactly `n` doubles for a data block that starts at `first_line`
 * (which must contain the "grid.data=" or "height.data=" prefix).
 *
 * file: open FILE* positioned at the line containing the "prefix" (or later).
 * first_line: buffer containing the current line (the one where prefix was found).
 * prefix: "grid.data=" or "height.data="
 * out: double array of length n (preallocated).
 * scratch: char buffer of size scratch_sz used for reading subsequent lines with fgets.
 *
 * Returns:
 *  0 on success (reads exactly n values into out),
 * -1 on error (incomplete data or malformed token),
 * -2 on allocation error.
 */
int read_n_doubles_from_stream(FILE *file,
                               char *first_line,
                               const char *prefix,
                               int n,
                               double *out,
                               char *scratch,
                               size_t scratch_sz)
{
    if (!file || !first_line || !prefix || n <= 0 || !out) return -1;

    // Build a dynamic accumulator string that will hold remaining text to parse.
    size_t acc_cap = scratch_sz * 2;
    char *acc = malloc(acc_cap);
    if (!acc) return -2;
    acc[0] = '\0';

    // Find prefix in first_line
    char *p = strstr(first_line, prefix);
    if (p) p += strlen(prefix);
    else p = first_line; // just in case

    // Initialize accumulator with the remainder of the first line after prefix
    size_t len_p = strlen(p);
    if (len_p + 1 > acc_cap) {
        char *tmp = realloc(acc, len_p + 1);
        if (!tmp) { free(acc); return -2; }
        acc = tmp; acc_cap = len_p + 1;
    }
    strcpy(acc, p);

    int filled = 0;
    char *parse_ptr = acc;
    errno = 0;

    while (filled < n) {
        // Skip whitespace at parse_ptr
        while (*parse_ptr && isspace((unsigned char)*parse_ptr)) parse_ptr++;

        // Attempt to parse with strtod
        char *endptr = NULL;
        errno = 0;
        double v = strtod(parse_ptr, &endptr);

        if (endptr && endptr != parse_ptr) {
            // Successfully parsed a number
            out[filled++] = v;
            parse_ptr = endptr;
            continue;
        }

        // No number parsed at current parse_ptr. We need more data.
        // If we've reached EOF of file -> error (incomplete)
        if (!fgets(scratch, (int)scratch_sz, file)) {
            // If parse_ptr contains only whitespace but no more input, it's incomplete
            // Determine how many we had and return error.
            free(acc);
            return -1;  // incomplete data
        }

        // Append scratch to accumulator, but preserve unparsed tail.
        // Compute unparsed tail start
        size_t tail_offset = parse_ptr - acc;  // index of tail start in acc
        size_t tail_len = strlen(acc + tail_offset);

        // New accumulator size needed
        size_t addlen = strlen(scratch);
        size_t need = tail_len + addlen + 1; // +1 null
        if (need + 32 > acc_cap) { // small slack
            size_t newcap = acc_cap * 2;
            while (newcap < tail_len + addlen + 1) newcap *= 2;
            char *tmp = realloc(acc, newcap);
            if (!tmp) { free(acc); return -2; }
            acc = tmp;
            acc_cap = newcap;
        }

        // Move the unparsed tail to the front of acc
        memmove(acc, acc + tail_offset, tail_len + 1); // include null
        // Append new scratch content
        strcat(acc, scratch);

        // Reset parse_ptr to beginning of acc
        parse_ptr = acc;
        continue;
    }

    free(acc);
    return 0;
}


//creating a radar, a polar box, and a radarscan type from the radar_scans file. 

void read_radar_scans(const char* filename) {
    scan_count = 0;
	FILE* file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open file");
        return;
    }

    char line[4096];
    int in_block = 0;

    // Temporary vars
    int scan_index = 0;
    double scan_time = 0.0;
    int radar_id = 0;
    char freq[2] = "", mode[4] = "";
    double x=0,y=0,z=0,max_range=0,range_res=0,angular_res=0;
    double min_gate=0, max_gate=0, min_angle=0, max_angle=0;
    double num_ranges=0, num_angles=0;
    int grid_size = 0;
    double* grid_data = NULL;
    double other_angle = 0;
    int height_size = 0;
    double* height_data = NULL;

    while (fgets(line, sizeof(line), file)) {
        if (strstr(line, "=== BEGIN RADAR_SCAN ===")) {
            in_block = 1;
            // Reset vars
            scan_index = radar_id = 0;
	    scan_time = 0.0;
            freq[0] = '\0'; mode[0] = '\0';
            x = y = z = max_range = range_res = angular_res = 0;
            min_gate = max_gate = min_angle = max_angle = other_angle = 0;
            num_ranges = num_angles = 0;
            grid_size = 0;
            free(grid_data); grid_data = NULL;
	    height_size = 0;
	    free(height_data);height_data=NULL;
    	    continue;
        }

        if (strstr(line, "=== END RADAR_SCAN ===")) {
            in_block = 0;

            Radar* radar = get_or_create_radar(radar_id, freq, mode, x, y, z,
                                               max_range, range_res, angular_res);
            Polar_box* box = create_polar_box(radar_id,mode, min_gate, max_gate,
                                              min_angle, max_angle, num_ranges,
                                              num_angles, range_res, angular_res,
                                              grid_size, other_angle, grid_data,height_size,height_data);

            radar_scans[scan_count].scan_index = scan_index;
	    radar_scans[scan_count].time = scan_time;
	    radar_scans[scan_count].radar = radar;
            radar_scans[scan_count].box = box;
            scan_count++;
grid_size = 0;
            free(grid_data); grid_data = NULL;
	    height_size = 0;
	    free(height_data);height_data=NULL;

            continue;
        }

        if (!in_block) continue;

        // Parse lines
        if (sscanf(line, "scan.index=%d", &scan_index)) continue;
        if (sscanf(line, "scan.time=%lf", &scan_time)) continue;
	if (sscanf(line, "radar.id=%d", &radar_id)) continue;
        if (sscanf(line, "radar.frequency=%1s", freq)) continue;
        if (sscanf(line, "radar.scanning_mode=%3s", mode)) continue;
        if (sscanf(line, "radar.x=%lf", &x)) continue;
        if (sscanf(line, "radar.y=%lf", &y)) continue;
        if (sscanf(line, "radar.z=%lf", &z)) continue;
        if (sscanf(line, "radar.maximum_range=%lf", &max_range)) continue;
        if (sscanf(line, "radar.range_resolution=%lf", &range_res)) continue;
        if (sscanf(line, "radar.angular_resolution=%lf", &angular_res)) continue; 
	//if (sscanf(line, "box.radar_id=%d", &radar_id)) continue;
        //if (sscanf(line, "box.scanning_mode=%3s", mode)) continue;
	if (sscanf(line, "box.min_range_gate=%lf", &min_gate)) continue;
        if (sscanf(line, "box.max_range_gate=%lf", &max_gate)) continue;
        if (sscanf(line, "box.min_angle=%lf", &min_angle)) continue;
        if (sscanf(line, "box.max_angle=%lf", &max_angle)) continue;
        if (sscanf(line, "box.num_ranges=%lf", &num_ranges)) continue;
        if (sscanf(line, "box.num_angles=%lf", &num_angles)) continue;
        if (sscanf(line, "box.range_resolution=%lf", &range_res)) continue;
        if (sscanf(line, "box.angular_resolution=%lf", &angular_res)) continue;
        if (sscanf(line, "box.other_angle=%lf", &other_angle)) continue;

        if (sscanf(line, "grid.size=%d", &grid_size)) {
            if (grid_size > 0) {
                grid_data = (double*)malloc(sizeof(double) * grid_size);
                if (!grid_data) {
                    printf("Memory allocation failed for grid.\n");
                    fclose(file);
                    return;
                }
            }
	printf("I updated the grid memory allocation file: %s, scan %d\n", filename, scan_index);
            continue;
        }

	if (sscanf(line, "height.size=%d", &height_size)) {
	    if (height_size > 0) {
	        height_data = (double*)malloc(sizeof(double) * height_size);
	        if (!height_data) {
	            printf("Memory allocation failed for height.\n");
	            fclose(file);
	            return;
	        }
	    }
	printf("I updated the height memory allocation\n");
	    continue;
	}

	// before loop: allocate a scratch buffer of decent size
char scratch[8192];  // can be larger; used for incremental reads

// when you detect grid.data=
if (strstr(line, "grid.data=") && grid_size > 0) {
    if (!grid_data) {
        fprintf(stderr, "grid_data not allocated but grid.size=%d\n", grid_size);
        // optionally allocate here or error out
    } else {
        int rc = read_n_doubles_from_stream(file, line, "grid.data=", grid_size, grid_data, scratch, sizeof(scratch));
        if (rc != 0) {
            fprintf(stderr, "Failed to read grid.data for scan %d (rc=%d)\n", scan_index, rc);
            // handle error: free and abort or skip
            free(grid_data);
            grid_data = NULL;
            // you can choose to return or continue depending on policy
            fclose(file);
            return;
        }
    }
}	

if (strstr(line, "height.data=") && height_size > 0) {
    if (!height_data) {
        fprintf(stderr, "height_data not allocated but height.size=%d\n", height_size);
    } else {
        int rc = read_n_doubles_from_stream(file, line, "height.data=", height_size, height_data, scratch, sizeof(scratch));
 	if (rc != 0) {
            fprintf(stderr, "Failed to read height.data for scan %d (rc=%d)\n", scan_index, rc);
            free(height_data); height_data = NULL;
            fclose(file);
            return;
        }
    }
}
    }

    fclose(file);
}



Bounding_box* bounding_box_from_textfile(const Polar_box* p_box, const Radar* radar){
if(p_box==NULL){printf("create_bounding+box_for_polar_plot\n You are trying to create a bounding box for a polar box which is not defined (points to NULL)\n The bounding box will be assigned NULL\n\n");return NULL;}	
 

	Bounding_box* bbox = malloc(sizeof(Bounding_box));


	if(strcmp(p_box->scanning_mode, "PPI")==0){
//double rmin = p_box->min_range_gate * p_box->range_resolution;
double rmin = (p_box->min_range_gate * p_box->range_resolution);
double curvature_correction_min = cos(p_box->other_angle*DEG2RAD + atan2(rmin*cos(p_box->other_angle*DEG2RAD),(KEA+rmin*sin(p_box->other_angle*DEG2RAD))));
//double rmax = p_box->max_range_gate * p_box->range_resolution;
double rmax = p_box->max_range_gate * p_box->range_resolution;
double curvature_correction_max = cos(p_box->other_angle*DEG2RAD + atan2(rmax*cos(p_box->other_angle*DEG2RAD),(KEA+rmax*sin(p_box->other_angle*DEG2RAD))));
double anglemin = p_box->min_angle * p_box->angular_resolution * DEG2RAD;
double anglemax = p_box->max_angle * p_box->angular_resolution * DEG2RAD;
double anglemid = (anglemin + anglemax) / 2;
 
double xs[5] = {
    rmax * curvature_correction_max * cos(anglemin),
    rmin * curvature_correction_min * cos(anglemin),
    rmax * curvature_correction_max * cos(anglemax),
    rmin * curvature_correction_min * cos(anglemax),
    rmax * curvature_correction_max * cos(anglemid)
};
 
double ys[5] = {
    rmax * curvature_correction_max * sin(anglemin),
    rmin * curvature_correction_min * sin(anglemin),
    rmax * curvature_correction_max * sin(anglemax),
    rmin * curvature_correction_min * sin(anglemax),
    rmax * curvature_correction_max * sin(anglemid)

};
 
 
double xmin = xs[0], xmax = xs[0];
double ymin = ys[0], ymax = ys[0];
 
for (int i = 1; i < 5; ++i) {
    if (xs[i] < xmin) xmin = xs[i];
    if (xs[i] > xmax) xmax = xs[i];
    if (ys[i] < ymin) ymin = ys[i];
    if (ys[i] > ymax) ymax = ys[i];
}


                                   
Point* pos_radar = get_position_radar(radar);
                                   
                                   
// Allocate and fill the bounding box
//Bounding_box* bbox = malloc(sizeof(Bounding_box));
bbox->topLeft.x = xmin+pos_radar->x;
bbox->topLeft.y = ymax+pos_radar->y;
                                   
bbox->topRight.x = xmax+pos_radar->x;
bbox->topRight.y = ymax+pos_radar->y;
                                   
bbox->bottomLeft.x = xmin+pos_radar->x;
bbox->bottomLeft.y = ymin+pos_radar->y;
                                   
bbox->bottomRight.x = xmax+pos_radar->x;
bbox->bottomRight.y = ymin+pos_radar->y;

}

if(strcmp(p_box->scanning_mode,"RHI")== 0){

	double rmin = get_min_range_gate(p_box) * get_range_res_radar(radar);
	double rmax = get_max_range_gate(p_box) * get_range_res_radar(radar);
	double angleMin = get_min_angle(p_box) * DEG2RAD * get_angular_res_polar_box(p_box);
	double angleMax = get_max_angle(p_box) * DEG2RAD * get_angular_res_polar_box(p_box);
	
	double h_min = calculate_height_of_beam_at_range(rmin, angleMin, radar->z);
	double h_max = calculate_height_of_beam_at_range(rmax, angleMax, radar->z);
	double h_mid = calculate_height_of_beam_at_range(rmin, angleMax, radar->z);
	double h_midd = calculate_height_of_beam_at_range(rmax, angleMin,radar->z);

	double smin = KEA*asin((rmin*cos(angleMax))/(KEA+h_mid));
	double smax = KEA*asin((rmax*cos(angleMin))/(KEA+h_midd));

	double radar_dist_from_origin = sqrt(radar->x * radar->x + radar->y * radar->y);


//	Bounding_box* bbox = malloc(sizeof(Bounding_box));
	bbox->topLeft.x = radar_dist_from_origin + smin;
bbox->topLeft.y /*height or z coord */ = h_max;
	
	bbox->topRight.x = radar_dist_from_origin + smax;
	bbox->topRight.y /* height or z coord */= h_max;

	bbox->bottomLeft.x = radar_dist_from_origin + smin;
	bbox->bottomLeft.y /* height or z coord */ = h_min;

	bbox->bottomRight.x = radar_dist_from_origin + smax;
	bbox->bottomRight.y /* height or z coord */ = h_min;

}
return bbox;                       
                                   
}                                  

void free_polar_box(Polar_box *box) {
    if (!box) return;  // Safety check

    if (box->grid) {
        free(box->grid);
        box->grid = NULL;
    }

    if (box->height_grid) {
        free(box->height_grid);
        box->height_grid = NULL;
    }

    if (box->attenuation_grid) {
        free(box->attenuation_grid);
        box->attenuation_grid = NULL;
    }

    free(box);  // Finally, free the struct itself
}

// Function to generate Gaussian noise
double gaussian_noise(double mean, double stddev) {
    static int hasSpare = 0;
    static double spare;

    if (hasSpare) {
        hasSpare = 0;
        return mean + stddev * spare;
    }

    hasSpare = 1;
    double u, v, s;
    do {
        u = (rand() / ((double) RAND_MAX)) * 2.0 - 1.0;
        v = (rand() / ((double) RAND_MAX)) * 2.0 - 1.0;
        s = u * u + v * v;
    } while (s >= 1 || s == 0);

    s = sqrt(-2.0 * log(s) / s);
    spare = v * s;
    return mean + stddev * u * s;
}

// Function to add noise based on frequency
double add_noise(const Radar* radar, double reflectivity) {
    double noise_db = 0.0;

    if (strcmp(radar->frequency, "X") == 0) {
        noise_db = 3.0;
    } else if (strcmp(radar->frequency, "C") == 0) {
        noise_db = 1.0;
    } else {
        // Unknown frequency, no noise added
        return reflectivity;
    }

    // Add Gaussian noise with 0 mean and noise_db as standard deviation
    return reflectivity + gaussian_noise(0.0, noise_db);
}


// Compute specific attenuation [dB/km] using power law
double compute_specific_attenuation(double refl_dBZ, const Radar* radar) {
if (isnan(refl_dBZ) || isinf(refl_dBZ)) return 0.0;  // Already partially done

double Z_lin = pow(10.0, refl_dBZ / 10.0);

double a, b;
    if (strcmp(radar->frequency, "X") == 0) {
        a = A_COEFF_X;
        b = B_COEFF_X;
    } else if (strcmp(radar->frequency, "C") == 0) {
        a = A_COEFF_C;
        b = B_COEFF_C;
    } else {
        // Default: assume no attenuation
        return 0.0;
    }
// Avoid zero to negative exponent
if (Z_lin <= 0.0 && b < 0.0) return 0.0;  

double att = a * pow(Z_lin, b);
if (isnan(att) || isinf(att)) return 0.0;   // Safe fallback

    return (att*radar->range_resolution*0.001); // [dB]
}

double normalize_angle(double angle_deg) {
    double a = fmod(angle_deg, 360.0);
    if (a < 0) a += 360.0;
    return a;
}


