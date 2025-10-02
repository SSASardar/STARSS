/**
 * @file radars.h
 * @brief Structures, functions prototypes, and variables in the radar measurment models
 */



#ifndef RADARS_H
#define RADARS_H

// Including relevant header files and structures
#include "common.h"
#include <stdio.h>   // for FILE
#include <stddef.h>  // for size_t
struct Raincell; // from material_coords_raincell.h
struct Spatial_raincell; // from spatial_coords_raincell.h
struct VPR; // from vertical_profiles.h
struct VPR_params; // from vertical_profiles.h
struct Cart_grid; // from processing.h

/** @brief defining the maximum number of radar scans in the simulation */
#define MAX_SCANS 1000

/** @brief defining the maximum number of radars throughout the simulation */
#define MAX_RADARS 5

/** @brief Defining curve of the earth in a 4/3 earth radius model (a non-flat earth) */
#define KEA 1.333333333*6371000.0



/**
 * @defgroup XBandAttenuationCoefficients X-band attenuation coefficients
 * @brief Empirical attenuation coefficients for X-band radar.
 * Coefficients for k = a * Z^b [dB/km]   
 * Source: Hitschfeld & Bordan (1954)     
 *
 * @{
 */
#define A_COEFF_X 1.5e-5  /**< Coefficient a for X-band */
#define B_COEFF_X 1.02    /**< Exponent b for X-band */
/** @} */


/**
 * @defgroup CBandAttenuationCoefficients C-band attenuation coefficients
 * @brief Empirical attenuation coefficients for C-band radar.
 * Coefficients for k = a * Z^b [dB/km]   
 * Source: Hitschfeld & Bordan (1954)     
 * @{
 */
#define A_COEFF_C 1.5e-5
#define B_COEFF_C 0.80
/** @} */

/**
 * @struct Radar
 * @brief The speciications of a specific radar are stored in this structure
 */
typedef struct Radar {int id;/**< Unique Identifier*/
char frequency[2];/**< Keeping track of the frequency band (so far only C or X-band... single letters only please.)*/
char scanning_mode[4];/**< Specifies either a Plan Position Indicator (PPI) or a Range Height Indicator (RHI) as a measurement type*/
double x; /**< Location of the radar, x coordinate in Cartesian space.*/
double y;/**< Location of the radar, y coordinate in Cartesian space.*/
double z;/**< Location of the radar (height), z coordinate in Cartesian space.*/
double maximum_range; /**< Maximum range of the radar in meters */
double range_resolution; /**< the range resolution of the radar in meters */
double angular_resolution; /**< the angular resolution of radar in degrees */
} Radar;

/**
 * @struct Polar_box
 * @brief Storing the observed raincell with a minimal number of zero elements.
 *
 * depending on the orientation, the angle of the polar box changes in azimuth, or it changes in elevation.
 */
typedef struct Polar_box {
int radar_id;/**< iD of the radar making the measurement */
double min_range_gate;/**< the closest possible range-gate to the nearest point of the raincell from the radar. from 0 to max number of range gates.*/
double max_range_gate;/**< the closest possible range-gate to the farthest point of the raincell as seen from the radar. from 0 to max number of range gates.*/
double min_angle;/**< the smallest angle which captures the edge of the raincell from 0 to max number of angles it is the index in the range-angle data matrix.*/
double max_angle;/**< the largest angle which cpatures the edge of the raincell from 0 to max number of angles. it is the index in the range-angle data matrix */
int num_ranges; /**< a count of the number of ranges between min and max range */
int num_angles;/**< a count of the number of angles between the min and max angle */
double range_resolution; /**< the range resolution of the radar, taken from the radar structure*/
double angular_resolution;/**< the angular resolution of the radar in degrees */
double *grid;/**< the 1D matrix (element_id = radar_id*num_angles + angle_id) of the measurement made */
double other_angle;/**< storing either the elevation angle or azimuth angle in the PPI or RHI respectively */
double *height_grid; /**< storing the heights each sample is taken as. also a 1D matrix: (element_id=radar_id*num_angles+angle_id)*/
double *attenuation_grid; /**< storing the attenuation experienced at each range gate. also a 1D matrix: (element_id=radar_id*num_angles+angle_id)*/
} Polar_box;


/**
 * @struct RadarScan
 * @brief  structure to hold several radar scans for a volume scan
 */
typedef struct RadarScan {
	int scan_index;/**< The scan index in the volume scan */
	double time;/**< The time at which the PPI scan was made*/
	Radar* radar;/**< The radar used for the PPI scan */
        Polar_box* box;/**< the filled polar box for the PPI scan */
	struct Cart_grid* c_grid;/**< The interpolated cartesian grid around the Polar_box of the PPI scan*/
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
