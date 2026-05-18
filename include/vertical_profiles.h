// This is the header for the vertical profiles.c file
//
//
// The setup of all vertical information is done here. In the processing file, in the radars.c file the measuremnt noise can be included. 
//


/** 
 * @file vertical_profiles.h
 * @brief structures and function prototypes describing vertical profiles of reflectivities
 *
 */

#ifndef VERTICAL_PROFILES_H
#define VERTICAL_PROFILES_H

/**
 * @struct VPR_point
 * @brief A parametrisation point for a VPR
 *
 */
typedef struct VPR_point {
	double reflectivity;
	double height;
} VPR_point;


/**
 * @struct VPR
 * @brief VPRs parametrised by five (reflectivity,height) points
 *
 */
typedef struct VPR {
	VPR_point ET;
	VPR_point BB_u;
	VPR_point BB_m;
	VPR_point BB_l;
	VPR_point CB;
	VPR_point GT;
} VPR;

/**
 * @struct VPR_params
 * @brief Parametrisation of the development of extreme rainfall
 *
 * There are four stages ____, you still need to correct the naming thoughout the code.
 *
 */
typedef struct VPR_params {
	//time parameters
	double t_growth_start;/**< starting time phase 2*/
	double t_mature_start;/**< starting time phase 3*/
	double t_mature_end;/**< starting time phase 4*/
	double t_decay_mid;/**< time of peak rainfall intensity (during phase 4)*/
	double t_decay_end;/**< starting time phase */

	
	//	rates of growth
	double div_f_growth;
	double div_f_mature;
	double div_f_decay;
	double div_f_decay1;
	double div_f_decay2;

	// Echo Top parameters: nonchanging through different phases
	double Z_et_0;
	double h_et_0;
	double del_h_et;
	double h_above_ML;
	
	// bright band parameters:
	// 		 Everything is relative to the middle of the bright band which determines the height and the peak intensity
	// 	The heights and reflectivities of the top and bottom of the bright band are determined by their respective width parameters.
	// 	How the widths are distributed to the top and bottom are determined by the ratio parameters.
	double Z_bb_0;
	double del_Z_bb_growth;
	double del_Z_bb_mature;
	double del_Z_bb_decay;
	double h_bb_0;
	double del_h_bb_growth;
	double del_h_bb_mature;
	double width_Z_0;
	double del_width_Z_growth;
	double del_width_Z_mature;
	double width_h_0;
        double del_width_h_growth;
	double del_width_h_mature;

	//	ratio parameters:
	double ratio_U_to_L;
	double del_ratio_UL_growth;
	double del_ratio_UL_mature;
	double del_ratio_UL_decay;

	// cell base parameters: how the heights and reflectivities change in different phases.
	double Z_cb_0;
	double del_Z_cb_growth;
	double del_Z_cb_mature;
	double del_Z_cb_decay;
	double h_cb_0;
	double del_h_cb_growth;
	double del_h_cb_mature;
		
	// ground truth parameters:
	double gradient_from_CB; //so this is the same as the Cloud base multiplied by some gradient relative to height.
} VPR_params;


/** 
 * @var VPR_point sorted_points[5]
 * @brief Array of VPR points sorted by height (lowest to highest).
 *
 * This array contains 5 VPR points that are assumed to be ordered
 * from the lowest to the highest altitude. For a different parametrisation
 * with more points increase the size of this variable
 *
 */
VPR_point sorted_points[5];


/** 
 * @brief Initialises all VPR development parameters to zeros.
 */
void init_VPR_params(VPR_params *params);

/**
 * @brief Populates the VPR development parameters to the set values.
 *
 * With this function the whole process of how the rainfall develops can be configured.
 */
void fill_VPR_params(
    VPR_params *params,
    double t_growth_start, double t_mature_start, double t_mature_end,
    double t_decay_mid, double t_decay_end,
    double Z_et_0, /*double h_et_0,*/ double del_h_et, double h_above_ML,
    double Z_bb_0, double del_Z_bb_growth, double del_Z_bb_mature, double del_Z_bb_decay,
    double h_bb_0, double del_h_bb_growth, double del_h_bb_mature,
    double width_Z_0, double del_width_Z_growth, double del_width_Z_mature,
    double width_h_0, double del_width_h_growth, double del_width_h_mature,
    double ratio_U_to_L, double del_ratio_UL_growth, double del_ratio_UL_mature, double del_ratio_UL_decay,
    double Z_cb_0, double del_Z_cb_growth, double del_Z_cb_mature, double del_Z_cb_decay,
    double h_cb_0, double del_h_cb_growth, double del_h_cb_mature,
    double gradient_from_CB
);

/**
 * @brief Allocate and initialise a new VPR on the heap.
 *
 * @return pointer to newly allocated VPR, or NULL on failure.
 *         Caller is responsible for freeing it with free().
 */
VPR *create_VPR(void);

/**
 * @brief Allocate and initialise a new VPR set to the stratiform profile on the heap.
 *
 * @return pointer to newly allocated VPR, or NULL on failure. Set to stratiform vertical profile.
 *         Caller is responsible for freeing it with free().
 */
VPR *create_and_fill_VPR(const VPR_params *params);

/**
 * @brief Computing the convective VPR based on the stratiform VPR and the VPR development parameters.
 *
 * @return pointer to recomputed convective VPR at the given time.
 *  
 */
void update_VPR(const VPR *vpr, const VPR_params *params, double time, VPR *vpr_conv);

/**
 * @brief [DEBUG] print the parametrisation of the VPR called (5 points)
 */
void print_VPR_points(const VPR* vpr);

/**
 * @brief linear interpolator between the points of parametrisation of the VPR for ease
 */
double interpolate_reflectivity(VPR_point p1, VPR_point p2, double height);

/**
 * @brief computing the reflectivity at a given height based on the interpolation and the VPR parametrisation
 */
double get_reflectivity_at_height(const VPR *vpr, double height);

/**
 * @defgroup VPRArithmetic VPR arithmetic
 * @brief Functions for manipulating and computing VPR structures.
 *
 * These functions perform arithmetic operations and climatological
 * calculations on Vertical Profile of Reflectivity (VPR) data.
 * @{
 */

/**
 * @brief Add the values of one VPR into another.
 *
 * @param[in]  src   Source VPR.
 * @param[out] dest  Destination VPR to accumulate into.
 */
void cumaddVPR(const VPR *src, VPR *dest);

/**
 * @brief Divide all values in a VPR by a divisor.
 *
 * @param[in,out] vpr     VPR to modify.
 * @param[in]     divisor Divisor value.
 */
void divideVPR(VPR *vpr, int divisor);

/**
 * @brief Add a scaled VPR into another.
 *
 * @param[in]  src    Source VPR.
 * @param[out] dest   Destination VPR to accumulate into.
 * @param[in]  scale  Scale factor applied to src before adding.
 */
void cumaddVPR_scale(const VPR *src, VPR *dest, double scale);

/**
 * @brief Multiply all values in a VPR by a scalar.
 *
 * @param[in,out] vpr    VPR to modify.
 * @param[in]     scalar Scalar multiplier.
 */
void multiplyVPR(VPR *vpr, double scalar);

/**
 * @brief Compute an average VPR over a time interval.
 *
 * @param[out] vpr_avg  Output average VPR.
 * @param[in]  params   Parameters controlling the VPR model.
 * @param[in]  t_start  Start time.
 * @param[in]  t_end    End time.
 * @param[in]  dt       Time step.
 * @param[in]  scratch  Scratch VPR buffer for intermediate results.
 */
void compute_average_VPR(VPR *vpr_avg, VPR_params *params,
                         double t_start, double t_end,
                         double dt, VPR *scratch);

/**
 * @brief Reset a VPR to zero.
 *
 * @param[out] vpr  VPR to reset.
 */
void zeroVPR(VPR *vpr);

/**
 * @brief Compute a climatological VPR.
 *
 * @param[out] vpr_clima   Output climatology VPR.
 * @param[in]  params      Parameters controlling the VPR model.
 * @param[in]  dt          Time step.
 * @param[in]  strat_tail  Proportion of time the rainfall follows the stratiform after its convective rain has stopped.
 * @param[in]  scratch     Scratch VPR buffer for intermediate results.
 */
void compute_climatology_VPR(VPR *vpr_clima, VPR_params *params,
                             double dt, double strat_tail,
                             VPR *scratch);

/** @} */ // end of VPRArithmetic

int print_vpr_interpolated(const VPR *vpr, const char *filename, int append); 
#endif // VERTICAL_PROFILES_H
