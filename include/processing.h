#ifndef PROCESSING_H
#define PROCESSING_H

#include <stdbool.h>
#include <stddef.h> 
#include "common.h"
#include "radars.h"
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "vertical_profiles.h"

/**
 * @struct Cart_grid
 * @brief Storing a 2-D cartesian grid with squares. 
 *
 *
 */
typedef struct Cart_grid {
	double resolution;/**< resolution of the square dx=dy */
	double *grid;/**< pointer storing the measured reflectivity values*/
	double *height_grid;/**< pointer storing the heights of the measured reflectivity*/
	double *estimated_attenuation_grid;/**< pointer storing the path-integrated attenuation*/
	int *rain_type_grid;/**< pointer storing the integer classification of the rain type*/
	int num_elements;/**<storing number of gridpoints*/
	int num_x;/**< storing the number in axis 1 (x)*/
	int num_y;/**< storing the number in axis 2 (y or z)*/
	Point ref_point;/**< storing the left bottom corner of the cartesian box*/
} Cart_grid;


/**
 * @struct Vol_scan
 * @brief Storing a set of PPI's as 1 volume scan.
 */
typedef struct Vol_scan {
    int num_PPIs;/**< storing the number of PPI's in the volume scan*/
    size_t num_elements;/**< storing the total number of elements in one PPI.*/
    size_t num_x;/**< storing the number of elements in axis 1 (x) in one PPI*/
    size_t num_y;/**< storing the number of elements in axis 2 (y) in one PPI*/
    Point ref_point;/**< storing the most left bottom corner of all the PPI's*/
    double resolution;/**< storing the resolution of the PPI's/Volume scan. This should be the same*/

    double *grid_refl;/**< storing the reflectivity measurements in a pointer of size = num_elements * num_PPIs*/
    double *grid_height; /**< storing the heights of the reflectivity measurements in a pointer*/
    double *grid_att; /**< storing the the path-integrated attenuation of the reflectivity measurements in a pointer*/
    int *grid_rain_type;/**<storing the rainfall classes for each point*/
    //double *quality_metric; /**< storing the quality metric of each point*/
    double *display_grid;/**< storing the projected data (of size = num_elements in PPI) in a pointer.*/
double *refl_ALA;       /**<storing the reflectivity at lowest altitude*/
double emp_vpr_strat[120]; /**<storing (num_points_in_grid, reflectivity) the empirical stratiform VPR of size 40*3 */
double emp_vpr_conv[120]; /**<storing (num_points_in_grid, reflectivity) the empirical convective VPR of size 40*3 */


} Vol_scan;

Cart_grid* Cart_grid_init(double resolution, int num_x, int num_y, Point ref_point);

double normalizeAngle(double angle); // angle in radians.

bool isAngleBetween(double angle, double minAngle, double maxAngle);


bool isPointInSectorAnnulus(Point p, Point center, double minAngle, double maxAngle, double minRange, double maxRange); 


double f(double x, double radar_height, double surface_range, double height_above_radar,FILE *fp);
double df(double x, double radar_height, double surface_range, double height_above_radar);

int newton_bisection(
    double a,
    double b,
    double x0,
    double tol,
    int max_iter,
    double *root,
    double radar_height,
    double surface_range,
    double height_above_radar
    );

int brent_root(
    double a,
    double b,
    double tol,
    int max_iter,
    double *root,
    double radar_height,
    double surface_range,
    double height_above_radar,
    FILE *fp
);


double r1(double theta, double s, double k_eA, double h);
double r2(double theta, double k_eA, double h);
double r_diff(double theta, double s, double k_eA, double h);
double solve_theta(double s, double k_eA, double h,
                   double theta_min, double theta_max);

bool getPolarBoxIndex(Point p, double c_x, double c_y,const Polar_box* box, int *range_idx, int *angle_idx);


void writeCartGridToFile(Cart_grid* cg, int scan_id, int what_to_print); 

Vol_scan *init_vol_scan(Cart_grid **cart_grids, int num_PPIs);

static inline int vol_index(const Vol_scan *vol, int x, int y, int ppi) {
    return ppi * vol->num_elements + x * vol->num_y + y;
}

Cart_grid* interpolate_scan_NN(Polar_box *p_box, Radar *radar, double time, 
                                double cart_grid_res, int scan_idx, int slice_idx);

int add_cart_grid_to_volscan(Vol_scan *vol, Cart_grid *grid, int ppi_index);

void free_vol_scan(Vol_scan *vol);


int write_vol_scan_ppi_to_file(const Vol_scan *vol, int ppi_index, const char *filename);

void save_volscan_grid_to_file(const Vol_scan* vol, int scan_index, double scan_time, const char* grid_type, const char* filename);
 

int compute_display_grid_KNMI(Vol_scan *vol, double threshold, const VPR *vpr_strat ,const VPR *vpr_conv);

double compute_ground_to_altitude_ratio(const VPR *vpr, double height);

double compute_ground_to_altitude_diff(const VPR *vpr, double height);

double sigmoid_three_point(double p1, double p2, double p3);
double height_quality_metric_KNMI(double height, double h_l, double h_m, double h_h);

double quality_reduction_KNMI(double x, double x_0);



int compute_display_grid_average(Vol_scan *vol, double threshold);
int compute_display_grid_max(Vol_scan *vol, double threshold);
int compute_display_grid_lowest_valid_height(Vol_scan *vol, double threshold);



int write_display_grid_to_file(const Vol_scan *vol, const char *filename); 
int write_true_grid_to_file(const Vol_scan *vol, const char *filename); 

int classify_point_in_raincell(const Point *pt, const Point *raincell_center, const Raincell *raincell); 
int fill_refl_ALA_grid(Vol_scan *vol, const Point *raincell_center, const Raincell *raincell, const VPR *vpr_1, const VPR *vpr_2);

// Compute radar statistics and also unmasked total true rainfall
int compute_rainfall_statistics(const Vol_scan *vol,
                                double threshold,
                                double cart_grid_res,
                                double *mse,
                                double *mae,
                                double *bias,
                                double *total_measured,
                                double *total_true_masked,
                                double *total_measured_mm2,
                                double *total_true_mm2,
                                double *total_true_unmasked,
                                double *total_true_mm2_unmasked);


void free_cart_grid(Cart_grid *cg);


int save_vol_scan_to_file(Vol_scan *vol, const char *filename);

int save_vol_scan_to_text(Vol_scan *vol, const char *filename); 

void process_volume_scan_VPR(Vol_scan *vs);
void compute_average_empVPR(Vol_scan *vs);
void compute_std_dev_empVPR(Vol_scan *vs);
 

int print_vpr_profile(const Vol_scan *vs, const char *filename, int profile_type);
int print_vpr_detailed(const Vol_scan *vs, const char *filename, int profile_type, int append); 


double get_reflectivity_from_empirical_vpr_interp(const double *emp_vpr, double height, double bin_size_km, double ground_height_km); 
double get_stdev_from_empirical_vpr_interp(const double *emp_vpr, double height, double bin_size_km, double ground_height_km);
double compute_ground_to_altitude_diff_empirical(const Vol_scan *vol, double height, int rain_type, double bin_size_km, double ground_height_km);
int compute_display_grid_KNMI_empirical(Vol_scan *vol, double threshold, double bin_size_km, double ground_height_km);
 
int print_vpr_detailed_with_std(const Vol_scan *vs, const char *filename, int profile_type, int append);






#endif /* PROCESSING_H  */
