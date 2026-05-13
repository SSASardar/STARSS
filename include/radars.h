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
 * Source: https://essd.copernicus.org/articles/16/2317/2024/ 
 *
 * @{
 */
//#define A_COEFF_X 1.5e-5  /**< Coefficient a for X-band */
//#define B_COEFF_X 1.02    /**< Exponent b for X-band */
#define A_COEFF_X 6.27e-5  /**< Coefficient a for X-band */
#define B_COEFF_X 0.845    /**< Exponent b for X-band */
/** @} */


/**
 * @defgroup CBandAttenuationCoefficients C-band attenuation coefficients
 * @brief Empirical attenuation coefficients for C-band radar.
 * Coefficients for k = a * Z^b [dB/km]   
 * Source: https://journals.ametsoc.org/view/journals/atot/38/6/JTECH-D-20-0113.1.xml     
 * @{
 */
#define A_COEFF_C 7.215e-6
//#define A_COEFF_C 1.5e-5
#define B_COEFF_C 0.907
//#define B_COEFF_C 0.80
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
char scanning_mode[4];/**< Specifies either a Plan Position Indicator (PPI) or a Range Height Indicator (RHI) as a measurement type*/
double x; /**< Location of the radar, x coordinate in Cartesian space.*/
double y; /**< Location of the radar, y coordinate in Cartesian space.*/
double z; /**< Location of the radar, z coordinate in Cartesian space.*/
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
double *estimated_attenuation_grid; /**< storing the attenuation experienced at each range gate. also a 1D matrix: (element_id=radar_id*num_angles+angle_id)*/
int *rain_type;/**< the 1D matrix (element_id = radar_id*num_angles + angle_id) of the type of rain found made */
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
//	struct Cart_grid* c_grid;/**< The interpolated cartesian grid around the Polar_box of the PPI scan*/
} RadarScan;


/**
 * @brief Number of radar scans/slices in one volume scan
 *
 * This variable is defined in radar.c and is filled by reading the radar_scan_dddd.txt file
 *
 */
extern RadarScan radar_scans[MAX_SCANS];

/** @brief Storing the number of radars in the network
 *
 * This variable is defined in radar.c and needs to be filled in manually.
 *
 */
extern Radar* radar_list[MAX_RADARS];           
 
/** @ brief stores the number of radar scans/slices in the volume scan. 
 *
 * This is set when it is used. 
 */
extern int scan_count;

/** @brief stores the number of radars in the network
 *
 * Is updated every time it is used manually.
 */
extern int radar_count;




 /** @brief Creates and initialises a radar
  *
  * @param id the radar's unique id
  * @param frequency the radar's frequency (X or C)
  * @param scanning_mode the radar's scanning mode, choice of Plan Position Indicator (PPI) or Range Height Indicator (RHI). 
  * @param x the x-coordinate in the global coordinates
  * @param y the y-coordinate in the global coordinates
  * @param z the height at which the radar is placed
  * @param max_range the radar's maximum range
  * @param range_res the radar's range resolution
  * @param angular_res the radar's angular resolution (0.5, 1.0 and 2.0 degrees tested)
  * 
  * @return Radar struct which can be used in other functions.
  */
Radar* create_radar(int id, const char* frequency, const char* scanning_mode, double x, double y,double z, double max_range, double range_res, double angular_res);

/** @brief returns an existing radar or creates and initialises a new radar. 
 *
 * @param id the radar's unique id
 * @param frequency the radar's frequency (X or C)
 * @param scanning_mode the radar's scanning mode, choice of Plan Position Indicator (PPI) or Range Height Indicator (RHI). 
 * @param x the x-coordinate in the global coordinates
 * @param y the y-coordinate in the global coordinates
 * @param z the height at which the radar is placed
 * @param max_range the radar's maximum range
 * @param range_res the radar's range resolution
 * @param angular_res the radar's angular resolution (0.5, 1.0 and 2.0 degrees tested)
 * 
 * @return Radar struct which can be used in other functions.
 */
Radar* get_or_create_radar(int id, const char* freq, const char* mode, double x, double y, double z, double max_range, double range_res, double angular_res);

/** @brief Storing one radar scan/slice.
 *
 * @param radar_id which radar was scanned?
 * @param min_range_gate Smallest range gate which captures the raincell
 * @param max_range_gate Largest range gate which captures the raincell
 * @param min_angle Smallest angle (in degrees) which captures the raincell
 * @param max_angle Largest angle (in degrees) which captures the raincell
 * @param num_ranges stores the number of used range gates
 * @param num_angles stores the number of used angular gates
 * @param range_res stores the range resolution of the radar
 * @param angular_res stores the angular resolution of the radar
 * @param grid_size stores the number of range gates across all angles used
 * @param other_angle stores either the elevation angle or the azimuth angle depending on the scanning mode
 * @param grid_data stores the measured reflectivity
 * @param height_size stores the size of the storage matrix height_data
 * @param height_data stores the heights at which the reflectivity is measured at
 *
 * @return Polar_box which can be written to to store information.
 */
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
     int estimated_attenuation_size,
    double *estimated_attenuation_data,
    int height_size,
    double *height_data,
    int *rain_type
    );

/**
 * @brief for reuse of allocated polar box
 *
 * @return Polar_box to reuse
 */
Polar_box* init_polar_box();

/** @brief used to update the other angle in an existing Polar_box
 *
 * Once you have a measurment loaded in a Polar_box, and you want to move to a new measurement, first change the fixed angle at which it scans, then repeat a measurement. 
 *
 * @param p_box an existing Polar_box to be used in the new measurements
 * @param new_angle the new fixed angle. 
 */
void update_other_angle(Polar_box* p_box, double new_angle);


/** @brief function which executes the radar measurements of the raincell. 
 *
 * @param polar_box the Polar_box which will store the measurement. 
 * @param time the time of the measurement (ASSUMPTION: the whole scan is conducted at the same time.)
 * @param s_raincell the spatial description of the raincell containing its speed and initial location in both x and y
 * @param radar the radar which conducts the measurement
 * @param raincell the material description of the raincell containing its vertical evolution and the location of the intense developing core
 *
 * @return 0 if successful, -1 if there is an error along with an error message
 */
int fill_polar_box(Polar_box* polar_box, double time, const struct Spatial_raincell* s_raincell, const Radar* radar, const struct Raincell* raincell, const struct VPR_params* params);

/**
 * @brief [DEBUG] prints out the radar specifications so you can check... 
 *
 * @param radar the radar you want to check 
 */ 
void print_radar_specs(const Radar* radar);


/** 
 * @brief gets the x-y position of the radar
 *
 * @param radar the radar you want to check
 */
Point* get_position_radar(const Radar* radar);


/** 
 * @brief gets height of the radar
 *
 * @param radar the radar you want to check
 */
double get_height_of_radar(const Radar* radar);


/** 
 * @brief gets the range resolution of the radar in meters
 *
 * @param radar the radar you want to check
 */
double get_range_res_radar(const Radar* radar);


/** 
 * @brief gets the angular resolution of the radar (in degrees)
 *
 * @param radar the radar you want to check
 */
double get_angular_res_radar(const Radar* radar);


/** 
 * @brief gets the maximum range of the radar in meters
 *
 * @param radar the radar you want to check
 */
double get_max_range_radar(const Radar* radar);


/** 
 * @brief gets the unique identifier of the radar
 *
 * @param radar the radar you want to check
 */
int get_radar_id(const Radar* radar);


/** 
 * @brief gets the frequency band of the radar in letters
 *
 * @param radar the radar you want to check
 */
const char* get_frequency(const Radar* r);


/** 
 * @brief gets the scanning mode of the radar (PPI or RHI)
 *
 * @param radar the radar you want to check
 */
const char* get_scanning_mode(const Radar*);

/**
 * @brief [DEBUG] prints the corners of the polar box
 *
 * @param box the Polar_box being checked.
 */
void print_polar_box(const Polar_box* box);


// Getter function declarations

/** 
 * @brief retrieving the radar id a polar box has saved data from. 
 *
 * @param box the Polar_box being checked.
 */
int get_radar_id_for_polar_box(const struct Polar_box* box);

/** 
 * @brief retrieving the minimum range gate of the polar box. 
 *
 * @param box the Polar_box being checked.
 */
double get_min_range_gate(const struct Polar_box* box);

/** 
 * @brief retrieving the maximum range gate of the polar box. 
 *
 * @param box the Polar_box being checked.
 */
double get_max_range_gate(const struct Polar_box* box);

/** 
 * @brief retrieving the minimum angle of the polar box. 
 *
 * @param box the Polar_box being checked.
 */
double get_min_angle(const struct Polar_box* box);

/** 
 * @brief retrieving the maximum angle of the polar box. 
 *
 * @param box the Polar_box being checked.
 */
double get_max_angle(const struct Polar_box* box);

/** 
 * @brief how many range gates per angle are saved in the polar box?. 
 *
 * @param box the Polar_box being checked.
 */
double get_num_ranges(const struct Polar_box* box);

/** 
 * @brief How many angles are included in the polar box?. 
 *
 * @param box the Polar_box being checked.
 */
double get_num_angles(const struct Polar_box* box);

/** 
 * @brief What is the range resolution in the polar box?. 
 *
 * @param box the Polar_box being checked.
 */
double get_range_res_polar_box(const struct Polar_box* box);

/** 
 * @brief What is the angular resolution of the polar box? 
 *
 * @param box the Polar_box being checked.
 */
double get_angular_res_polar_box(const struct Polar_box* box);

/**
 * @brief query the radar which the polar box saved data from.
 *
 * @param box the Polar_box
 * @param radars an array of all radars in the system
 * @param num_radars the number of radars in the whole system
 */
const Radar* find_radar_by_id(const Polar_box* box, const Radar** radars, int num_radars);

/**
 * @brief querying a radar with only it's unique identifier.
 *
 * @param idA the id of the radar you want to find.
 */
const Radar* find_radar_by_id_ONLY(int idA);


Bounding_box* create_bounding_box_for_polar_box(const Polar_box* p_box, const Radar** radars, int num_radars);
Bounding_box* create_bounding_box_for_polar_box_EZ(const Polar_box* p_box);

double calculate_height_of_beam_at_range(double range, double elevation, double height_of_radar);


int sample_from_relative_location_in_raincell(double range, double angle, double elevation, const Point* radar_centre, const Point* spatial_centre, const struct Raincell* raincell);

void fill_polar_box_grid(struct Polar_box* box, const struct Radar* radar, const struct Spatial_raincell* s_raincell, const struct Raincell* raincell, double time, const struct VPR *vpr_strat, const struct VPR *vpr_conv);

void save_polar_box_grid_to_file(const Polar_box* box, const Radar* radar, int scan_index,double scan_time, const char* filename);

int read_n_ints_from_stream(FILE *file, const char *prefix, int n, int *out);


int read_n_doubles_from_stream(FILE *file,const char *prefix,int n,double *out);
//int read_n_doubles_from_stream(FILE *file,char *first_line,const char *prefix,int n,double *out,char *scratch,size_t scratch_sz);
void read_radar_scans(const char* filename);

Bounding_box* bounding_box_from_textfile(const Polar_box* p_box, const Radar* radar);

double gaussian_noise(double mean, double stddev);
double add_noise(const Radar* radar, double reflectivity);

double add_noise_VPR(double reflectivity);
double add_noise_SA(const Radar* radar, double attenuation); 
double compute_specific_attenuation(double refl_dBZ, const Radar* radar);

double normalize_angle(double angle_deg);

//FREEING STUFF

void free_polar_box(Polar_box *box);

#endif /* RADARS_H */
