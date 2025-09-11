// This is the header file for radars.c
//
//
//
//
//




#ifndef RADARS_H
#define RADARS_H

#include "common.h"
#include <stdio.h>   // for FILE
#include <stddef.h>  // for size_t
		     //
		     //
struct Raincell;
struct Spatial_raincell;
struct VPR;
struct VPR_params;
struct Cart_grid;

#define MAX_SCANS 1000
#define MAX_RADARS 5
#define KEA 1.333333333*6371000.0


// Example coefficients for k = a * Z^b [dB/km]
// Literature values: no real values
// X-band: a ≈ ?, b ≈ ?
// C-band: a ≈ ?, b ≈ ?
// Source: Hitschfeld & Bordan (1954)
#define A_COEFF_X 1.5e-5
#define B_COEFF_X 1.02
#define A_COEFF_C 1.5e-5
#define B_COEFF_C 0.80


typedef struct Radar {int id;
char frequency[2];
char scanning_mode[4];
double x;
double y;
double z;
double maximum_range;
double range_resolution;
double angular_resolution;
} Radar;

typedef struct Polar_box {
int radar_id;
double min_range_gate;
double max_range_gate;
double min_angle;
double max_angle;
int num_ranges;
int num_angles;
double range_resolution;
double angular_resolution;
double *grid;
double other_angle;
double *height_grid;
double *attenuation_grid;
} Polar_box;

typedef struct RadarScan {
	int scan_index;
	double time;
	Radar* radar;
        Polar_box* box;
	struct Cart_grid* c_grid;
} RadarScan;



extern RadarScan radar_scans[MAX_SCANS];
extern Radar* radar_list[MAX_RADARS];           
 
extern int scan_count;
extern int radar_count;





Radar* create_radar(int id, const char* frequency, const char* scanning_mode, double x, double y,double z, double max_range, double range_res, double angular_res);


Radar* get_or_create_radar(int id, const char* freq, const char* mode, double x, double y, double z, double max_range, double range_res, double angular_res);



//Polar_box* create_polar_box(double time, const Spatial_raincell* s_raincell, const Radar* radar, const Raincell* raincell);

//Polar_box* create_polar_box(int radar_id, double min_range_gate, double max_range_gate,double min_angle, double max_angle, double num_ranges,double num_angles, double range_res, double angular_res,int grid_size, double *grid_data);

Polar_box* create_polar_box(
    int radar_id,
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
    );


Polar_box* init_polar_box();
void update_other_angle(Polar_box* p_box, double new_angle);
int fill_polar_box(Polar_box* polar_box, double time, const struct Spatial_raincell* s_raincell, const Radar* radar, const struct Raincell* raincell);

void print_radar_specs(const Radar* radar);

Point* get_position_radar(const Radar* radar);
double get_height_of_radar(const Radar* radar);
double get_range_res_radar(const Radar* radar);

double get_angular_res_radar(const Radar* radar);

double get_max_range_radar(const Radar* radar);

int get_radar_id(const Radar* radar);

const char* get_frequency(const Radar* r);

const char* get_scanning_mode(const Radar*);



/*void print_polar_grid(const Polar_box* polar_box, const Radar** radars, int num_radars);
*/

void print_polar_box(const Polar_box* box);


// Getter function declarations
int get_radar_id_for_polar_box(const struct Polar_box* box);
double get_min_range_gate(const struct Polar_box* box);
double get_max_range_gate(const struct Polar_box* box);
double get_min_angle(const struct Polar_box* box);
double get_max_angle(const struct Polar_box* box);
double get_num_ranges(const struct Polar_box* box);
double get_num_angles(const struct Polar_box* box);
double get_range_res_polar_box(const struct Polar_box* box);
double get_angular_res_polar_box(const struct Polar_box* box);


const Radar* find_radar_by_id(const Polar_box* box, const Radar** radars, int num_radars);
const Radar* find_radar_by_id_ONLY(int idA);
Bounding_box* create_bounding_box_for_polar_box(const Polar_box* p_box, const Radar** radars, int num_radars);
Bounding_box* create_bounding_box_for_polar_box_EZ(const Polar_box* p_box);

double calculate_height_of_beam_at_range(double range, double elevation, double height_of_radar);


int sample_from_relative_location_in_raincell(double range, double angle, double elevation, const Point* radar_centre, const Point* spatial_centre, const struct Raincell* raincell);

void fill_polar_box_grid(struct Polar_box* box, const struct Radar* radar, const struct Spatial_raincell* s_raincell, const struct Raincell* raincell, double time, const struct VPR *vpr_strat, const struct VPR *vpr_conv);

void save_polar_box_grid_to_file(const Polar_box* box, const Radar* radar, int scan_index,double scan_time, const char* filename);
int read_n_doubles_from_stream(FILE *file,char *first_line,const char *prefix,int n,double *out,char *scratch,size_t scratch_sz);
void read_radar_scans(const char* filename);

Bounding_box* bounding_box_from_textfile(const Polar_box* p_box, const Radar* radar);

double gaussian_noise(double mean, double stddev);
double add_noise(const Radar* radar, double reflectivity);
double compute_specific_attenuation(double refl_dBZ, const Radar* radar);

double normalize_angle(double angle_deg);

//FREEING STUFF

void free_polar_box(Polar_box *box);

#endif /* RADARS_H */
