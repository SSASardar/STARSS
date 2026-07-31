// this is the processing.c file to implement processing of the radar data. 
//
//


// include statements:
#include "processing.h"
#include "spatial_coords_raincell.h"
#include "material_coords_raincell.h"
#include "common.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <ctype.h>
#include <float.h>


#define MAX_ALLOWED_CELLS ((size_t)1e9)  // ~1 billion doubles = ~8 GB


#ifndef KEA
#define KEA = 1.333333333 * 6371000.0
#endif



Cart_grid* Cart_grid_init(double resolution, int num_x, int num_y, Point ref_point) {
    Cart_grid *cg = (Cart_grid *)malloc(sizeof(Cart_grid));
    if (!cg) return NULL;

    cg->resolution = resolution;
    cg->num_x = num_x;
    cg->num_y = num_y;
    cg->num_elements = num_x * num_y;
    cg->ref_point = ref_point;

    cg->grid = (double *)malloc(sizeof(double) * cg->num_elements);
    cg->height_grid = (double *)malloc(sizeof(double)*cg->num_elements);
    cg->estimated_attenuation_grid = (double *)malloc(sizeof(double) * cg->num_elements);
    cg->rain_type_grid= (int *)malloc(sizeof(int) * cg->num_elements);
    //if(cg->rain_type_grid)printf("allocating integer pointer (for an array of integers) is successful\n");
    
    if (!cg->grid) {
        free(cg);
	printf("Allocating grid in Cart_grid_init() failed! allocating NULL!! \n");
        return NULL;
    }

    for (int i = 0; i < cg->num_elements; i++) {
        cg->grid[i] = 0.0;
    	cg->height_grid[i] = 0.0;
    	cg->estimated_attenuation_grid[i]=0.0;
	cg->rain_type_grid[i] = 9;
    }
	//printf("success I think? \n");
    return cg;
}

// Normalize angle to [0, 2*PI)
double normalizeAngle(double angle) {
    while (angle < 0) angle += 2 * M_PI;
    while (angle >= 2 * M_PI) angle -= 2 * M_PI;
    return angle;
}

// Check if angle is between minAngle and maxAngle, considering wrapping
bool isAngleBetween(double angle, double minAngle, double maxAngle) {
    angle = normalizeAngle(angle);
    minAngle = normalizeAngle(minAngle);
    maxAngle = normalizeAngle(maxAngle);

    if (minAngle <= maxAngle) {
        return angle >= minAngle && angle <= maxAngle;
    } else {
        // Sector crosses the 0 angle line
        return angle >= minAngle || angle <= maxAngle;
    }
}

// Check if a point is inside the sector annulus with arbitrary center
bool isPointInSectorAnnulus(Point p, Point center, double minAngle, double maxAngle, double minRange, double maxRange) {
    // Translate the point relative to the center
    double dx = p.x - center.x;
    double dy = p.y - center.y;

    // Compute polar coordinates relative to the center
    double r = sqrt(dx * dx + dy * dy);
    if (r < minRange || r > maxRange) {
        return false;
    }

    double angle = atan2(dy, dx);     // Angle relative to center
    angle = normalizeAngle(angle);    // Convert to [0, 2*PI)

    return isAngleBetween(angle, minAngle, maxAngle);
}

/* r1(theta) */
double r1(double theta, double s, double k_eA, double h)
{
    return sin(s / k_eA) * (k_eA + h) / cos(theta);
}

/* r2(theta) */
double r2(double theta, double k_eA, double h)
{
    double term = k_eA * sin(theta);
    return -term + sqrt(term * term + h * h + 2.0 * h * k_eA);
}

/* r2(theta) - r1(theta) */
double r_diff(double theta, double s, double k_eA, double h)
{
    return r2(theta, k_eA, h) - r1(theta, s, k_eA, h);
}

/*
 * Brent's method root finder
 * Solves r_diff(theta) = 0 on [theta_min, theta_max]
 */
double solve_theta(double s, double k_eA, double h,
                   double theta_min, double theta_max)
{
    const int max_iter = 100;
    const double tol = 1e-12;

    double a = theta_min;
    double b = theta_max;
    double c = b;
    double fa = r_diff(a, s, k_eA, h);
    double fb = r_diff(b, s, k_eA, h);
    double fc = fb;

    if (fa * fb >= 0.0) {
	    fprintf(stderr,"|  a  |  b  |  c  |  fa |  fb |  fc |\n");
	    fprintf(stderr,"| %.3e| %.3e| %.3e| %.3e| %.3e| %.3e|\n", a, b, c, fa, fb,fc);
        fprintf(stderr, "Root not bracketed\n");
       	exit(EXIT_FAILURE);
    }

    double d = 0.0, e = 0.0;

    for (int iter = 0; iter < max_iter; iter++) {

        if ((fb > 0 && fc > 0) || (fb < 0 && fc < 0)) {
            c = a;
            fc = fa;
            d = e = b - a;
        }

        if (fabs(fc) < fabs(fb)) {
            a = b;  b = c;  c = a;
            fa = fb; fb = fc; fc = fa;
        }

        double tol1 = 2.0 * tol * fabs(b) + 0.5 * tol;
        double xm = 0.5 * (c - b);

        if (fabs(xm) <= tol1 || fb == 0.0) {
            return b;
        }

        if (fabs(e) >= tol1 && fabs(fa) > fabs(fb)) {
            double s1 = fb / fa;
            double p, q;

            if (a == c) {
                p = 2.0 * xm * s1;
                q = 1.0 - s1;
            } else {
                double q1 = fa / fc;
                double r1 = fb / fc;
                p = s1 * (2.0 * xm * q1 * (q1 - r1) - (b - a) * (r1 - 1.0));
                q = (q1 - 1.0) * (r1 - 1.0) * (s1 - 1.0);
            }

            if (p > 0.0) q = -q;
            p = fabs(p);

            if (2.0 * p < fmin(3.0 * xm * q - fabs(tol1 * q), fabs(e * q))) {
                e = d;
                d = p / q;
            } else {
                d = xm;
                e = d;
            }
        } else {
            d = xm;
            e = d;
        }

        a = b;
        fa = fb;

        if (fabs(d) > tol1)
            b += d;
        else
            b += (xm > 0 ? tol1 : -tol1);

        fb = r_diff(b, s, k_eA, h);
    }

    fprintf(stderr, "Maximum iterations exceeded\n");
    exit(EXIT_FAILURE);
}


double solve_theta_with_expansion(double s, double k_eA, double h,
                                   double theta_min, double theta_max,
                                   double tolerance) {

    const int max_expansions = 20;
    const double expansion_factor = 1.5;
    const int max_iter = 100;

    double a = theta_min;
    double b = theta_max;
    double fa = r_diff(a, s, k_eA, h);
    double fb = r_diff(b, s, k_eA, h);

    // Check if already at root
    if (fabs(fa) < tolerance) return a;
    if (fabs(fb) < tolerance) return b;

    // Expand bracket until sign change found or max expansions reached
    int expansions = 0;
    while (fa * fb > 0 && expansions < max_expansions) {
        double range = b - a;

        // Expand in the direction where function is smaller (closer to zero)
        if (fabs(fa) < fabs(fb)) {
            // Expand left
            a = a - range * expansion_factor;
            fa = r_diff(a, s, k_eA, h);
        } else {
            // Expand right
            b = b + range * expansion_factor;
            fb = r_diff(b, s, k_eA, h);
        }

        expansions++;

        // Check if we hit root during expansion
        if (fabs(fa) < tolerance) return a;
        if (fabs(fb) < tolerance) return b;
    }

    // If still no sign change, try scanning for any sign change
    if (fa * fb > 0) {
        double scan_start = -M_PI_2;  // -90 degrees
        double scan_end = M_PI_2;      // +90 degrees
        int num_scans = 100;
        double step = (scan_end - scan_start) / num_scans;

        double prev_theta = scan_start;
        double prev_val = r_diff(prev_theta, s, k_eA, h);

        for (int i = 1; i <= num_scans; i++) {
            double curr_theta = scan_start + i * step;
            double curr_val = r_diff(curr_theta, s, k_eA, h);

            if (prev_val * curr_val < 0) {
                a = prev_theta;
                b = curr_theta;
                fa = prev_val;
                fb = curr_val;
                break;
            }

            if (fabs(curr_val) < tolerance) return curr_theta;

            prev_theta = curr_theta;
            prev_val = curr_val;
        }
    }

    // Final check - if still no sign change, function may have no root
    if (fa * fb > 0) {
        fprintf(stderr, "Warning: No sign change found after expansion\n");
        fprintf(stderr, "Returning best guess (midpoint)\n");
        return (a + b) / 2.0;
    }

    // Brent's method with adaptive tolerance
    double c = b;
    double fc = fb;
    double d = 0.0, e = 0.0;

    for (int iter = 0; iter < max_iter; iter++) {
        // Use larger tolerance for larger values
        double adaptive_tol = tolerance * fmax(1.0, fabs(b));

        if ((fb > 0 && fc > 0) || (fb < 0 && fc < 0)) {
            c = a;
            fc = fa;
            d = e = b - a;
        }

        if (fabs(fc) < fabs(fb)) {
            a = b;  b = c;  c = a;
            fa = fb; fb = fc; fc = fa;
        }

        double tol1 = 2.0 * adaptive_tol * fabs(b) + 0.5 * adaptive_tol;
        double xm = 0.5 * (c - b);

        if (fabs(xm) <= tol1 || fb == 0.0) {
            return b;
        }

        if (fabs(e) >= tol1 && fabs(fa) > fabs(fb)) {
            double s_val = fb / fa;
            double p, q;

            if (a == c) {
                p = 2.0 * xm * s_val;
                q = 1.0 - s_val;
            } else {
                double q1 = fa / fc;
                double r1 = fb / fc;
                p = s_val * (2.0 * xm * q1 * (q1 - r1) - (b - a) * (r1 - 1.0));
                q = (q1 - 1.0) * (r1 - 1.0) * (s_val - 1.0);
            }

            if (p > 0.0) q = -q;
            p = fabs(p);

            if (2.0 * p < fmin(3.0 * xm * q - fabs(tol1 * q), fabs(e * q))) {
                e = d;
                d = p / q;
            } else {
                d = xm;
                e = d;
            }
        } else {
            d = xm;
            e = d;
        }

        a = b;
        fa = fb;

        if (fabs(d) > tol1) {
            b += d;
        } else {
            b += (xm > 0 ? tol1 : -tol1);
        }

        fb = r_diff(b, s, k_eA, h);

        // Early exit if we're close enough
        if (fabs(fb) < tolerance) {
            return b;
        }
    }

    fprintf(stderr, "Warning: Max iterations reached, returning best guess\n");
    return b;
}


bool getPolarBoxIndex(Point p,
                      double c_x,
                      double c_y,
                      const Polar_box *box,
                      int *range_idx,
                      int *angle_idx)
{
    if (!box || !range_idx || !angle_idx) {printf("no box, range id or angle id\n");return false;}

    const double eps = 1e-8; // small tolerance for floating point errors

	if(strcmp(box->scanning_mode, "PPI")==0){
    // --- Vector from radar to point ---
    double dx = p.x - c_x;
    double dy = p.y - c_y;

    // --- Slant range --- THERE IS A MISTAKE WITH THE SLANT RANGE AND THE SURFACE RANGE... 
    double r = sqrt(dx*dx + dy*dy);

    double r_min = box->min_range_gate * box->range_resolution;
    double r_max = box->max_range_gate * box->range_resolution;

    if (r < r_min - eps || r > r_max + eps) {/*printf("I am below or above the min and max range of the scan+++++++++++");*/return false;}


    // --- Angle in [0, 2π) ---
    double angle = atan2(dy, dx);
    if (angle < 0) angle += 2*M_PI;

    double min_angle = box->min_angle * box->angular_resolution * DEG2RAD;
    if (min_angle < 0) min_angle += 2*M_PI;

    double span = box->num_angles * box->angular_resolution * DEG2RAD;

    double angle_diff = fmod(angle - min_angle + 2*M_PI, 2*M_PI);
    if (angle_diff > span + eps) {/*printf("I have a larger angle than the angle range in the scan+++++++++");*/return false;}


    // --- Range index (round to nearest) ---
    *range_idx = (int)floor((r - r_min) / box->range_resolution + 1e-8);
    if (*range_idx < 0) *range_idx = 0;
    if (*range_idx >= (int)box->num_ranges) *range_idx = box->num_ranges - 1;

    // --- Angle index (round to nearest) ---
    *angle_idx = (int)floor(angle_diff / (box->angular_resolution * DEG2RAD + 1e-8));
    if (*angle_idx < 0) *angle_idx = 0;
    if (*angle_idx >= (int)box->num_angles) *angle_idx = box->num_angles - 1;

	
    return true;
}


    if(strcmp(box->scanning_mode, "RHI")==0){
    double r_min = box->min_range_gate * box->range_resolution;
    double r_max = box->max_range_gate * box->range_resolution;

    double eps = 1e-8;

	double h = sqrt((p.y-c_y)*(p.y-c_y));
	//double s = p.x-sqrt((box->x*box->x)+(box->y*box->y));
	double s = p.x;
//	printf("(s,h) = (%.2lf, %.2lf)\n", s,h);
	if(s>1e6) return false;
//	double angle_elevation = solve_theta(s,KEA,h,-1.5,1.5);
	double angle_elevation = solve_theta_with_expansion(s,KEA,h,-1.5,1.5,1e-8);
	if(angle_elevation>1.58 || angle_elevation<-1.58 || angle_elevation == 0.0){
		printf("%.2lf in radians 1.5 rad is 86 degree\n", angle_elevation);
	}
	//angle_elevation = acos(sin(s/KEA) * (KEA + h)/(box->min_range_gate*box->range_resolution));	

//FILE *fp = fopen("outputs/elevation_angles.txt", "a");
//if (!fp) {
//    perror("Failed to open output file");
//    return false;
//}



    double range_solved = sin(s/(KEA))*(KEA+h)/cos(angle_elevation);
    double range_solved_1 = -1*(KEA*sin(angle_elevation))+sqrt((KEA*sin(angle_elevation)*KEA*sin(angle_elevation))+h*h + 2*KEA*h);
    //fprintf(fp," a_zero = %.3e, r_solved = %.3e\n", angle_elevation, range_solved);
    *range_idx = (int)floor((range_solved - r_min) / box->range_resolution + 1e-8);
    //int range_id_other = (int)floor((range_solved - r_min) / box->range_resolution + 1e-8);



    if (*range_idx < 0) *range_idx = 0;
   // if (*range_idx < (int)box->min_range_gate) {
	   // printf("1");
	    //return false;}
    //if (*range_idx > (int)box->max_range_gate) {
//	    printf("(s,h) = (%.2lf,%.2lf), angle = %.2lf, range = %.2lf, %d,in [%d, %d]\n\n",s,h,angle_elevation, range_solved, *range_idx, (int)box->min_range_gate, (int)box->max_range_gate);
//	    return false;}
    if (*range_idx >= (int)box->num_ranges){ *range_idx = box->num_ranges - 1; return false;}
    
/*
double x_rThresh_a = box->x + cos(box->other_angle*DEG2RAD)*r_min;
double x_rThresh_b = box->x + cos(box->other_angle*DEG2RAD)*r_max;

double y_rThresh_a = box->y + sin(box->other_angle*DEG2RAD)*r_min;
double y_rThresh_b = box->y + sin(box->other_angle*DEG2RAD)*r_max;

double dist_a = sqrt((x_rThresh_a*x_rThresh_a)+(y_rThresh_a*y_rThresh_a));
double dist_b = sqrt((x_rThresh_b*x_rThresh_b)+(y_rThresh_b*y_rThresh_b));

double dist_min, dist_max;
if (dist_a <= dist_b) { dist_min = dist_a; dist_max = dist_b; } else {dist_min = dist_b; dist_max = dist_a;}

    if (range_solved < dist_min  || range_solved > dist_max){
	return false;
	} else {
	printf("(range in [rmin, rmax] --> %lf in [%lf, %lf]\n", range_solved, dist_min, dist_max);}
	printf("height = %.2lf, slant range = %.2lf, elevation_angle = %.2lf, range = %.2lf\n", h, s, angle_elevation,range_solved);	
  
*/      
	double min_angle = box->min_angle * box->angular_resolution;
    if (min_angle < 0) min_angle += 2*M_PI;

    double span = box->num_angles * box->angular_resolution;

    double angle_diff = fmod(angle_elevation - min_angle, 2*M_PI);
    if (angle_diff > span){
    	printf("angle_diff = %lf\n", angle_diff);
    	return false;
    }


    // --- Angle index (round to nearest) ---
    *angle_idx = (int)floor(angle_diff / (box->angular_resolution*DEG2RAD + 1e-8));
    if (*angle_idx < 0){ *angle_idx = 0; return false;}
    if (*angle_idx > (int)box->num_angles){ *angle_idx = box->num_angles - 1; return false;}

//Normalising to [0,max_idx] for both angle and range: 

//*angle_idx = *angle_idx-(int)box->min_angle;
//*range_idx = *range_idx-(int)box->min_range_gate;


//fprintf(fp,"+++++++++++++++++++++++++ RESULT ++++++++++++++++++++++++++\n");
//fprintf(fp,"++ angle_id = %d ++ range_id = %d ++ other range_id = %d ++\n", &angle_idx, &range_idx, range_id_other);
//fprintf(fp,"___________________________________________________________\n");
//fclose(fp);
//    return true;
//} else {
//fprintf(fp,"Root finding failed (code %d)\n", status);
//fprintf(fp,"___________________________________________________________\n");
//fclose(fp);
//    return false;
//}
//fclose(fp);
//printf("+++++1++++++++\n");
return true;
	}

    //return false;
    return true;
}


void writeCartGridToFile(Cart_grid* cg, int scan_id, int what_to_print) {
    if (!cg || !cg->grid) {
        printf("Error: Null Cart_grid or grid.\n");
        return;
    }
char filename[100];

//snprintf(filename, sizeof(filename), "outputs/cartesian_grid_output_%d.txt", scan_id);
if (what_to_print == 0) snprintf(filename, sizeof(filename), "outputs/m_cartesian_grid_output_%d.txt", scan_id);

if (what_to_print == 1) snprintf(filename, sizeof(filename), "outputs/h_cartesian_grid_output_%d.txt", scan_id);

if (what_to_print == 2) snprintf(filename, sizeof(filename), "outputs/a_cartesian_grid_output_%d.txt", scan_id);
if (what_to_print == 3) snprintf(filename, sizeof(filename), "outputs/t_cartesian_grid_output_%d.txt", scan_id);





FILE *fp = fopen(filename, "w");
    if (!fp) {
        printf("Error: Unable to open file for writing.\n");
        return;
    }

    for (int x =0; x<cg->num_x; x++) {
        for (int y =0;y< cg->num_y; y++) {
            int index = x * cg->num_y + y;
	    if (what_to_print == 0) fprintf(fp, "%.2f ", cg->grid[index]);  // format as needed
            if (what_to_print == 1) fprintf(fp, "%.2f ", cg->height_grid[index]);  // format as needed
    	    if (what_to_print == 2) fprintf(fp,  "%.2f ", cg->estimated_attenuation_grid[index]);    
    	    if (what_to_print == 3) fprintf(fp,  "%d ", cg->rain_type_grid[index]);    
    }
        fprintf(fp, "\n");  // newline after each row
    }

    fclose(fp);
    printf("Grid successfully written to cartesian_grid_output.txt\n");
}

Vol_scan *init_vol_scan(Cart_grid **cart_grids, int num_PPIs) {
    if (!cart_grids || num_PPIs <= 0) return NULL;

    Vol_scan *vol = (Vol_scan *)malloc(sizeof(Vol_scan));
    if (!vol) return NULL;

    vol->num_PPIs = num_PPIs;

    double min_x = DBL_MAX, min_y = DBL_MAX;
    double max_x = -DBL_MAX, max_y = -DBL_MAX;

    for (int i = 0; i < num_PPIs; i++) {
        Cart_grid *g = cart_grids[i];
        if (!g) continue;

        if (g->ref_point.x < min_x) min_x = g->ref_point.x;
        if (g->ref_point.y < min_y) min_y = g->ref_point.y;

        double g_max_x = g->ref_point.x + g->resolution * (g->num_x - 1);
        double g_max_y = g->ref_point.y + g->resolution * (g->num_y - 1);

        if (g_max_x > max_x) max_x = g_max_x;
        if (g_max_y > max_y) max_y = g_max_y;
    }

    vol->ref_point.x = min_x;
    vol->ref_point.y = min_y;

    double res = cart_grids[0]->resolution;
    size_t nx = (size_t)ceil((max_x - min_x) / res) + 1;
    size_t ny = (size_t)ceil((max_y - min_y) / res) + 1;
    size_t num_elements = nx * ny;

    // Debug logging of grid calculation
//    fprintf(stderr,
//        "[DEBUG] init_vol_scan:\n"
//        "  min_x=%.2f, max_x%.2f, min_y=%.2f, max_y=%.2f\n"
//        "  resolution=%.4f → nx=%zu, ny=%zu → total=%zu cells\n"
//        "  num_PPIs=%d → total_cells=%zu\n",
//        min_x, max_x, min_y, max_y,
//        res, nx, ny, num_elements,
//        num_PPIs, num_elements * (size_t)num_PPIs);

    // Sanity check
    if (num_elements > MAX_ALLOWED_CELLS || num_elements * (size_t)num_PPIs > MAX_ALLOWED_CELLS) {
        fprintf(stderr,
            "Error: volume too large (%zu cells across %d PPIs)\n",
            num_elements, num_PPIs);
        free(vol);
        return NULL;
    }

    vol->num_x = nx;
    vol->num_y = ny;
    vol->num_elements = num_elements;
    vol->resolution = res;

    size_t total_cells = num_elements * (size_t)num_PPIs;

    vol->grid_refl    = calloc(total_cells, sizeof(double));
    vol->grid_height  = calloc(total_cells, sizeof(double));
    vol->grid_att     = calloc(total_cells, sizeof(double));
    vol->grid_rain_type     = calloc(total_cells, sizeof(int));
    vol->display_grid = calloc(num_elements, sizeof(double));
    vol->refl_ALA     = calloc(num_elements, sizeof(double));

    if (!vol->grid_refl || !vol->grid_height || !vol->grid_att ||
        !vol->display_grid || !vol->refl_ALA) {
        free(vol->grid_refl); free(vol->grid_height); free(vol->grid_att);
        free(vol->display_grid); free(vol->refl_ALA); free(vol);
        return NULL;
    }

    for (size_t i = 0; i < total_cells; i++) {
        vol->grid_refl[i]   = NAN;
        vol->grid_height[i] = NAN;
        vol->grid_att[i]    = NAN;
    }

    for (size_t i = 0; i < num_elements; i++) {
        vol->display_grid[i] = NAN;
        vol->refl_ALA[i]     = NAN;
    }

    return vol;
}

Cart_grid* interpolate_scan_NN(Polar_box *p_box, Radar *radar, double time, 
                                double cart_grid_res, int scan_idx, int slice_idx) {
    if (!p_box || !radar) return NULL;
    
    // Create bounding box from radar coverage
    Bounding_box* bbox = bounding_box_from_textfile(p_box, radar);
    if (!bbox) return NULL;
    
    // Calculate grid dimensions
    int num_x = (int)(ceil((bbox->bottomRight.x - bbox->bottomLeft.x) / cart_grid_res));
    int num_y = (int)(ceil((bbox->topLeft.y - bbox->bottomLeft.y) / cart_grid_res));
    
    if (num_x <= 0) num_x = 1;
    if (num_y <= 0) num_y = 1;
    
    // Set reference point (bottom-left corner aligned to grid resolution)
    Point ref_point = {
        ceil(bbox->bottomLeft.x / cart_grid_res) * cart_grid_res,
        ceil(bbox->bottomLeft.y / cart_grid_res) * cart_grid_res
    };
    
    // Initialize Cartesian grid
    Cart_grid *cg = Cart_grid_init(cart_grid_res, num_x, num_y, ref_point);
    if (!cg) {
        free(bbox);
        return NULL;
    }
    
    // Statistics for debugging
    int valid_count = 0;
    int invalid_range = 0;
    int invalid_angle = 0;
    
    // Interpolate each point in the Cartesian grid
    for (int xi = 0; xi < num_x; xi++) {
        for (int yi = 0; yi < num_y; yi++) {
            int idA = xi * num_y + yi;
            
            // Calculate Cartesian coordinates of this grid point
            Point p = {
                ref_point.x + xi * cart_grid_res,
                ref_point.y + yi * cart_grid_res
            };
            
            int range_idx, angle_idx;
            
            // Convert Cartesian to polar coordinates and get indices
            if (getPolarBoxIndex(p, radar->x, radar->y, p_box, &range_idx, &angle_idx)) {
                valid_count++;
                int p_grid_idx = range_idx * (int)p_box->num_angles + angle_idx;
                
                // Copy values from polar grid to Cartesian grid
                cg->grid[idA] = p_box->grid[p_grid_idx];
                cg->height_grid[idA] = p_box->height_grid[p_grid_idx];
                cg->estimated_attenuation_grid[idA] = p_box->estimated_attenuation_grid[p_grid_idx];
                cg->rain_type_grid[idA] = p_box->rain_type[p_grid_idx];
            } else {
                // Point is outside radar coverage
                double dx = p.x - radar->x;
                double dy = p.y - radar->y;
                double r = sqrt(dx*dx + dy*dy);
                
                double r_min = p_box->min_range_gate * p_box->range_resolution;
                double r_max = p_box->max_range_gate * p_box->range_resolution;
                
                if (r < r_min || r > r_max)
                    invalid_range++;
                else
                    invalid_angle++;
                
                // Set to NAN for invalid points
                cg->grid[idA] = NAN;
                cg->height_grid[idA] = NAN;
                cg->estimated_attenuation_grid[idA] = NAN;
                cg->rain_type_grid[idA] = 9;  // 9 = undefined type
            }
        }
    }
    
    // Print statistics if needed (optional)
    // printf("Scan %d, Slice %d: Valid=%d, Invalid range=%d, Invalid angle=%d\n",
    //        scan_idx, slice_idx, valid_count, invalid_range, invalid_angle);
    
    free(bbox);
    return cg;
}

Cart_grid* interpolate_scan_NN_RHI(Polar_box *p_box, Radar *radar, double time, 
                                double cart_grid_res, int scan_idx, int slice_idx) {
    if (!p_box || !radar) return NULL;
    
    // Create bounding box from radar coverage
    Bounding_box* bbox = bounding_box_from_textfile(p_box, radar);
    if (!bbox) return NULL;
    
    // Calculate grid dimensions
    int num_x = (int)(ceil((bbox->bottomRight.x - bbox->bottomLeft.x) / cart_grid_res));
    int num_y = (int)(ceil((bbox->topLeft.y - bbox->bottomLeft.y) / cart_grid_res));
    
    if (num_x <= 0) num_x = 1;
    if (num_y <= 0) num_y = 1;
    
    // Set reference point (bottom-left corner aligned to grid resolution)
    Point ref_point = {
        ceil(bbox->bottomLeft.x / cart_grid_res) * cart_grid_res,
        ceil(bbox->bottomLeft.y / cart_grid_res) * cart_grid_res
    };
   
	printf("====================\n==================\n");
	printf("reference point (x,z)= (%.2lf,%.2lf)\n",ref_point.x,ref_point.y);
 


    // Initialize Cartesian grid
    Cart_grid *cg = Cart_grid_init(cart_grid_res, num_x, num_y, ref_point);
    if (!cg) {
        free(bbox);
        return NULL;
    }
    
    // Statistics for debugging
    int valid_count = 0;
    int invalid_range = 0;
    int invalid_angle = 0;
    
    // Interpolate each point in the Cartesian grid
    for (int xi = 0; xi < num_x; xi++) {
        for (int yi = 0; yi < num_y; yi++) {
            int idA = xi * num_y + yi;
            
            // Calculate Cartesian coordinates of this grid point
            Point p = {
                ref_point.x + xi * cart_grid_res,
                ref_point.y + yi * cart_grid_res
            };
            
            int range_idx, angle_idx;
            
            // Convert Cartesian to polar coordinates and get indices
            if (getPolarBoxIndex(p, radar->x, radar->z, p_box, &range_idx, &angle_idx)) {
                valid_count++;
                int p_grid_idx = range_idx * (int)p_box->num_angles + angle_idx;
                
                // Copy values from polar grid to Cartesian grid
                cg->grid[idA] = p_box->grid[p_grid_idx];
                cg->height_grid[idA] = p_box->height_grid[p_grid_idx];
                cg->estimated_attenuation_grid[idA] = p_box->estimated_attenuation_grid[p_grid_idx];
                cg->rain_type_grid[idA] = p_box->rain_type[p_grid_idx];
            } else {
                // Point is outside radar coverage
                double dx = p.x - radar->x;
                double dy = p.y - radar->y;
                double r = sqrt(dx*dx + dy*dy);
                
                double r_min = p_box->min_range_gate * p_box->range_resolution;
                double r_max = p_box->max_range_gate * p_box->range_resolution;
                
                if (r < r_min || r > r_max)
                    invalid_range++;
                else
                    invalid_angle++;
                
                // Set to NAN for invalid points
                cg->grid[idA] = NAN;
                cg->height_grid[idA] = NAN;
                cg->estimated_attenuation_grid[idA] = NAN;
                cg->rain_type_grid[idA] = 9;  // 9 = undefined type
            }
        }
    }
    
    // Print statistics if needed (optional)
    // printf("Scan %d, Slice %d: Valid=%d, Invalid range=%d, Invalid angle=%d\n",
    //        scan_idx, slice_idx, valid_count, invalid_range, invalid_angle);
    
    free(bbox);
    return cg;
}


int add_cart_grid_to_volscan(Vol_scan *vol, Cart_grid *grid, int ppi_index) {
    if (!vol || !grid) return -1;
    if (ppi_index < 0 || ppi_index >= vol->num_PPIs) return -2;

// --- Resolution consistency check ---
    double tol = 1e-6;  // tolerance for floating-point comparison
    if (fabs(grid->resolution - vol->resolution) > tol) {
        fprintf(stderr,
                "Resolution mismatch: grid=%.6f vol=%.6f\n",
                grid->resolution, vol->resolution);
        return -3; // or handle gracefully
    }


    double res = grid->resolution;

        for (int x = 0; x < grid->num_x; x++) {
    for (int y = 0; y < grid->num_y; y++) {
            int local_idx = x * grid->num_y + y;
            double abs_x = grid->ref_point.x + x * res;
            double abs_y = grid->ref_point.y + y * res;

            int vol_x = (int)floor((abs_x - vol->ref_point.x) / res);
            int vol_y = (int)floor((abs_y - vol->ref_point.y) / res);

            if (vol_x < 0 || vol_x >= (int)vol->num_x || vol_y < 0 || vol_y >= (int)vol->num_y) continue;

            int vol_idx = vol_index(vol, vol_x, vol_y, ppi_index);
	  //  printf("local=(%d,%d) abs=(%.2f,%.2f) -> vol=(%d,%d)\n",x, y, abs_x, abs_y, vol_x, vol_y);
            
//	    printf("local=(%d,%d) abs=(%.2f,%.2f) "
  //     "-> vol=(%d,%d) using res=%.2f (vol_res=%.2f)\n",
    //   x, y, abs_x, abs_y, vol_x, vol_y, grid->resolution, vol->resolution);

//printf("local=(%d,%d) height=%.2f -> vol=(%d,%d)\n",
  //     x, y,
    //   grid->height_grid ? grid->height_grid[local_idx] : NAN,
//       vol_x, vol_y);	    
	    
	    vol->grid_refl[vol_idx]   = grid->grid ? grid->grid[local_idx] : NAN;
            vol->grid_height[vol_idx] = grid->height_grid ? grid->height_grid[local_idx] : NAN;
            vol->grid_att[vol_idx]    = grid->estimated_attenuation_grid ? grid->estimated_attenuation_grid[local_idx] : NAN; 
	    vol->grid_rain_type[vol_idx]   = grid->rain_type_grid ? grid->rain_type_grid[local_idx] : 9;
	    //if(vol->grid_att[vol_idx]>10.0) vol->grid_att[vol_idx] = 10.0;
        }
    }

    return 0;
}


void free_vol_scan(Vol_scan *vol) {
    if (!vol) return;
    free(vol->grid_refl);
    free(vol->grid_height);
    free(vol->grid_att);
    free(vol->display_grid);
    free(vol->grid_rain_type);
    free(vol);
}

int write_vol_scan_ppi_to_file(const Vol_scan *vol, int ppi_index, const char *filename) {
    if (!vol || !filename) return -1;
    if (ppi_index < 0 || ppi_index >= vol->num_PPIs) return -2;

    FILE *f = fopen(filename, "w");
    if (!f) return -3;

    fprintf(f, "# Vol_scan PPI slice %d\n", ppi_index);
    fprintf(f, "# Grid size: %zu x %zu\n", vol->num_x, vol->num_y);
    fprintf(f, "# Format: reflectivity height\n");

        for (int x = 0; x < (int)vol->num_x; x++) {
    for (int y = 0; y < (int)vol->num_y; y++) {
            int idx = vol_index(vol, x, y, ppi_index);
            double refl = vol->grid_refl[idx];
            double h    = vol->grid_height[idx];

            if (isnan(refl) || isnan(h)) fprintf(f, "NaN NaN ");
            else fprintf(f, "%.2f %.2f ", refl, h);
        }
        fprintf(f, "\n");
    }

    fclose(f);
    return 0;
}




/**
 * @brief Prints a specified grid from a volume scan to a file in 2D format
 * @param vol Pointer to the volume scan structure
 * @param scan_index Index/identifier for this scan
 * @param scan_time Timestamp of the scan
 * @param grid_type String specifying which grid to print ("refl", "height", "att", "rain_type", "display", "refl_ALA")
 * @param filename Output file name (appends if exists)
 */
void save_volscan_grid_to_file(const Vol_scan* vol, int scan_index, double scan_time, 
                                const char* grid_type, const char* filename) {
    FILE* fp = fopen(filename, "a");
    if (!fp) {
        perror("Failed to open output file");
        exit(EXIT_FAILURE);
    }
    
    // Determine which grid to print and its data type
    const double* double_grid = NULL;
    const int* int_grid = NULL;
    int is_int_grid = 0;
    char grid_name[32];
    
    if (strcmp(grid_type, "refl") == 0) {
        double_grid = vol->grid_refl;
        strcpy(grid_name, "reflectivity");
    } else if (strcmp(grid_type, "height") == 0) {
        double_grid = vol->grid_height;
        strcpy(grid_name, "height");
    } else if (strcmp(grid_type, "att") == 0) {
        double_grid = vol->grid_att;
        strcpy(grid_name, "attenuation");
    } else if (strcmp(grid_type, "rain_type") == 0) {
        int_grid = vol->grid_rain_type;
        is_int_grid = 1;
        strcpy(grid_name, "rain_type");
    } else if (strcmp(grid_type, "display") == 0) {
        double_grid = vol->display_grid;
        strcpy(grid_name, "display");
    } else if (strcmp(grid_type, "refl_ALA") == 0) {
        double_grid = vol->refl_ALA;
        strcpy(grid_name, "refl_ALA");
    } else {
        fprintf(stderr, "Error: Unknown grid type '%s'\n", grid_type);
        fprintf(fp, "Error: Unknown grid type '%s'\n", grid_type);
        fclose(fp);
        exit(EXIT_FAILURE);
    }
    
    // Write volume scan header
    fprintf(fp, "=== BEGIN VOLUME_SCAN ===\n");
    fprintf(fp, "scan.index=%d\n", scan_index);
    fprintf(fp, "scan.time=%lf\n", scan_time);
    fprintf(fp, "vol.num_PPIs=%d\n", vol->num_PPIs);
    fprintf(fp, "vol.num_x=%zu\n", vol->num_x);
    fprintf(fp, "vol.num_y=%zu\n", vol->num_y);
    fprintf(fp, "vol.num_elements_per_PPI=%zu\n", vol->num_elements);
    fprintf(fp, "vol.grid_type=%s\n", grid_name);
    fprintf(fp, "vol.ref_point.x=%.3f\n", vol->ref_point.x);
    fprintf(fp, "vol.ref_point.y=%.3f\n", vol->ref_point.y);
    fprintf(fp, "vol.resolution=%.6f\n", vol->resolution);
    
    // Print each PPI separately in 2D format
    for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
        fprintf(fp, "\n--- BEGIN PPI %d ---\n", ppi);
        fprintf(fp, "ppi.index=%d\n", ppi);
        fprintf(fp, "ppi.dimensions=%zux%zu\n", vol->num_x, vol->num_y);
        
        if (!is_int_grid) {
            // Double grid - print as 2D matrix
            fprintf(fp, "%s.data.2D=\n", grid_name);
            for (size_t x = 0; x < vol->num_x; x++) {
                for (size_t y = 0; y < vol->num_y; y++) {
                    int idx = vol_index(vol, x, y, ppi);
                    if (isnan(double_grid[idx])) {
                        fprintf(fp, "NaN");
                    } else {
                        fprintf(fp, "%.2f", double_grid[idx]);
                    }
                    if (y < vol->num_y - 1) {
                        fprintf(fp, " ");
                    }
                }
                fprintf(fp, "\n");
            }
        } else {
            // Integer grid (rain_type) - print as 2D matrix
            fprintf(fp, "%s.data.2D=\n", grid_name);
            for (size_t x = 0; x < vol->num_x; x++) {
                for (size_t y = 0; y < vol->num_y; y++) {
                    int idx = vol_index(vol, x, y, ppi);
                    fprintf(fp, "%d", int_grid[idx]);
                    if (y < vol->num_y - 1) {
                        fprintf(fp, " ");
                    }
                }
                fprintf(fp, "\n");
            }
        }
        
        fprintf(fp, "--- END PPI %d ---\n", ppi);
    }
    
    fprintf(fp, "=== END VOLUME_SCAN ===\n\n");
    
    fclose(fp);
}

/*
int compute_display_grid_KNMI(Vol_scan *vol, double threshold, const VPR *vpr_strat ,const VPR *vpr_conv) {

// Add this debug code
double test_Q = quality_reduction_KNMI(0, 3);  // Should be 1.0
double test_Q2 = quality_reduction_KNMI(10, 3); // Should be very small
printf("quality_reduction_KNMI(0,3)=%.2e\n", test_Q);
printf("quality_reduction_KNMI(10,3)=%.2e\n", test_Q2);

double test_H = height_quality_metric_KNMI(2.0, 0.5, 1.0, 4.0);
printf("height_quality_metric=%.2e\n", test_H);


    if (!vol) return -1;
	    double Q_height = 0.0, Q_attenu = 0.0, Q_VPR = 0.0, Q_VPRunc = 0.0;
		double Z_projected = 0.0;
		double vpr_correction = 0.0;
	int counter_valid = 0, counter_invalid = 0;
    for (int x = 0; x < (int)vol->num_x; x++) {
    for (int y = 0; y < (int)vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;  // index into display_grid	
	    double dummy=0;
	    double dummy_quality = 0;
            int found = 0;
	    double Q_T = 0.0;

            for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
		double estim_pia = vol->grid_att[idx];
                double atten_correction = 2*estim_pia;
		if(atten_correction >10) atten_correction = 10;
		//vol->grid_refl[idx] = vol->grid_refl[idx] + atten_correction;		
		double refl = vol->grid_refl[idx] + atten_correction;
		double height = vol->grid_height[idx];
		
		

                if (!isnan(refl)) {
			
		Q_height = height_quality_metric_KNMI(height*0.001,0.5,1.0,4.0);
		Q_attenu = quality_reduction_KNMI(atten_correction,3);
		
		if(vol->grid_rain_type[idx] == (0 | 9)) Z_projected = 0.0;
		if(vol->grid_rain_type[idx] == 1) {
//			counter_valid++;
			vpr_correction = compute_ground_to_altitude_diff(vpr_strat,height);
			//if(counter_valid%100 == 0) {printf("vpr_correction is %.3e dB\n\n", vpr_correction);}
			Z_projected = refl+compute_ground_to_altitude_diff(vpr_strat,height);
			Q_VPR = quality_reduction_KNMI(fabs(compute_ground_to_altitude_diff(vpr_strat,height)),3); 
			//Z_projected = refl*compute_ground_to_altitude_ratio(vpr_strat,height);
			//Q_VPR = quality_reduction_KNMI(fabs(refl*(1-compute_ground_to_altitude_ratio(vpr_strat,height))),3); 
		}
		if(vol->grid_rain_type[idx] == 2){
//			counter_invalid++;
			vpr_correction = compute_ground_to_altitude_diff(vpr_conv,height);
			//if(counter_valid%100 == 0) {printf("vpr_correction is %.3e dB\n\n", vpr_correction);}
			Z_projected = refl+vpr_correction;
			Q_VPR = quality_reduction_KNMI(fabs(vpr_correction),3); 
	
			//Z_projected = refl*compute_ground_to_altitude_ratio(vpr_conv,height);
			//Q_VPR = quality_reduction_KNMI(fabs(refl*(1-compute_ground_to_altitude_ratio(vpr_conv,height))),3); 
	
		}
	
		double Z_projected_linear = pow(10.0, Z_projected*0.1);


		Q_T = (Q_attenu)*(Q_height)*(Q_VPR);
	//	if(Q_T<1e-5) continue;

		//	Q_T = 1.0;  // Override the product
		//Q_T = (1-Q_attenu)*(1-Q_height)*(1-Q_VPR);
//if(Q_T <= 0.0) continue;
//if(Q_T <0.01) {printf("(x,y,ppi) = (%d, %d, %d) \n\n\nAtten_corr = %.3e, At_corr_refl = %.3e, height = %.3e, vpr_correction = %.3e\n\n\n Q_atten = %.3e \n\n Q_height = %.3e \n\n Q_VPR = %.3e\n\n\n\n  Z_projected = %.3e\n\n\n",x, y, ppi, atten_correction, refl, height,vpr_correction, Q_attenu, Q_height, Q_VPR, Z_projected);	
//		pause_programme();
//		}
	


//if(Z_projected >30.0) {printf("(x,y,ppi) = (%d, %d, %d) \n\n\nAtten_corr = %.3e, At_corr_refl = %.3e, height = %.3e, vpr_correction = %.3e\n\n\n Q_atten = %.3e \n\n Q_height = %.3e \n\n Q_VPR = %.3e\n\n\n\n  Z_projected = %.3e\n\n\n",x, y, ppi, atten_correction, refl, height,vpr_correction, Q_attenu, Q_height, Q_VPR, Z_projected);	
//		pause_programme();}
			//dummy = dummy + refl;
                       //dummy = dummy + Z_projected;
                      	//dummy = dummy + Z_projected*Q_T;
                       	dummy = dummy + Z_projected_linear*(Q_T);
                        
			dummy_quality = dummy_quality + (Q_T);
			
			found = found + 1;
			
			Z_projected = 0.0;
			Q_attenu = 0.0;
			Q_height = 0.0;
			Q_VPR = 0.0;
			Q_T = 0.0;
			Z_projected_linear = 0.0;
                
		}
            }


		if( found == 0) {
			vol->display_grid[base_idx] = 0.0;
		       	//printf("no non-NaN values found in refl data for point (%d,%d) for the whole PPI\n", x, y);
			//counter_invalid++;
		} else {
			//counter_valid++;
	    //vol->display_grid[base_idx] = (dummy/(double)found < threshold) ? 0.0: dummy/(double)found;
	   //vol->display_grid[base_idx] = dummy/(double)found;
	    vol->display_grid[base_idx] = 10*log10(dummy/dummy_quality);
	    if(base_idx%10000 == 0) printf("f(%.3e/%.3e) = f(%.3e) = %.3e\n\n",dummy, dummy_quality, dummy/dummy_quality, 10*log10(dummy/dummy_quality));
		}
    }
    }
	printf("proportion of core / raincell = %.2f\n\n", (double)counter_invalid/(double)(counter_valid + counter_invalid));
    return 0;
}

*/
/*
int compute_display_grid_KNMI(Vol_scan *vol, double threshold, const VPR *vpr_strat, const VPR *vpr_conv) {
    if (!vol) return -1;
    
    double Q_height = 0.0, Q_attenu = 0.0, Q_VPR = 0.0, Q_VPRunc = 0.0;
    double Z_projected = 0.0;
    double vpr_correction = 0.0;
    int counter_valid = 0, counter_invalid = 0;
    
    // DEBUG counters
    int total_points_with_data = 0;
    int total_points_with_weights = 0;
    double min_weight = 1e10, max_weight = -1e10;
    
    for (int x = 0; x < (int)vol->num_x; x++) {
        for (int y = 0; y < (int)vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;
            double dummy = 0;
            double dummy_quality = 0;
            int found = 0;
            double Q_T = 0.0;
            
            // DEBUG: accumulate in linear space
            double sum_Z_linear = 0.0;
            double sum_weights = 0.0;
            int n_measurements = 0;
            
            for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
                double estim_pia = vol->grid_att[idx];
                double atten_correction = 2 * estim_pia;
                if(atten_correction > 10) atten_correction = 10;
                
                double refl = vol->grid_refl[idx] + atten_correction;
                double height = vol->grid_height[idx];
                
                if (!isnan(refl)) {
                    total_points_with_data++;
                    n_measurements++;
                    
                    Q_attenu = quality_reduction_KNMI(atten_correction, 3);
                    Q_height = fmin(height_quality_metric_KNMI(height*0.001, 0.5, 1.0, 4.0), 1.0);
                    
                    if(vol->grid_rain_type[idx] == 1) {
                        vpr_correction = compute_ground_to_altitude_diff(vpr_strat, height);
                        Z_projected = refl + vpr_correction;
                        Q_VPR = quality_reduction_KNMI(fabs(vpr_correction), 3);
                    } else if(vol->grid_rain_type[idx] == 2) {
                        vpr_correction = compute_ground_to_altitude_diff(vpr_conv, height);
                        Z_projected = refl + vpr_correction;
                        Q_VPR = quality_reduction_KNMI(fabs(vpr_correction), 3);
                    } else {
                        Z_projected = 0.0;
                        Q_VPR = 0.0;
                    }
                    
                    Q_T = Q_attenu * Q_height * Q_VPR;
                    
                    // Track weight extremes
                    if(Q_T < min_weight && Q_T > 0) min_weight = Q_T;
                    if(Q_T > max_weight) max_weight = Q_T;
                    
                    // DEBUG: Print problematic cases
                    if(Q_T < 1e-6 && Q_T > 0) {
                        printf("VERY SMALL WEIGHT at (x=%d,y=%d,ppi=%d): Q_T=%.2e\n", x, y, ppi, Q_T);
                        printf("  Q_attenu=%.2e, Q_height=%.2e, Q_VPR=%.2e\n", Q_attenu, Q_height, Q_VPR);
                        printf("  atten_correction=%.2f, height=%.2f, vpr_correction=%.2f\n", 
                               atten_correction, height, vpr_correction);
                        printf("  Z_projected=%.2f dBZ\n", Z_projected);
                    }
                    
                    // Method 1: Simple average (no weighting) for comparison
                    // Convert to linear for correct averaging
                    if(Z_projected > -10.0 && Q_T > 1e-9) {  // Lower threshold
                        double Z_linear = pow(10.0, Z_projected / 10.0);
                        sum_Z_linear += Z_linear;
                        sum_weights += 1.0;  // Unweighted for comparison
                        total_points_with_weights++;
                    }
                    
                    found++;
                    
                    Z_projected = 0.0;
                    Q_attenu = 0.0;
                    Q_height = 0.0;
                    Q_VPR = 0.0;
                    Q_T = 0.0;
                }
            }
            
            // Calculate display value
            if (sum_weights > 0) {
                double Z_linear_avg = sum_Z_linear / sum_weights;
                dummy = 10.0 * log10(Z_linear_avg);
                
                // DEBUG: Print suspicious outputs
                if(dummy > 100 || dummy < -50) {
                    printf("PROBLEM at (x=%d,y=%d): dummy=%.2f dBZ, n_meas=%d\n", x, y, dummy, n_measurements);
                    printf("  sum_Z_linear=%.2e, sum_weights=%.2f, Z_avg_linear=%.2e\n", 
                           sum_Z_linear, sum_weights, Z_linear_avg);
                }
            } else {
                dummy = -999.0;  // Fill value
            }
            
            // Store in display grid (assuming you have one)
            // vol->display_grid[base_idx] = dummy;
        }
    }
    
    // Print summary statistics
    printf("DEBUG SUMMARY:\n");
    printf("  Total points with data: %d\n", total_points_with_data);
    printf("  Total points with weights > threshold: %d\n", total_points_with_weights);
    printf("  Min weight: %.2e, Max weight: %.2e\n", min_weight, max_weight);
    
    return 0;
}

*/


/*

   int compute_display_grid_KNMI(Vol_scan *vol, double threshold, const VPR *vpr_strat, const VPR *vpr_conv) {
    if (!vol) return -1;
    
    double Q_height = 0.0, Q_attenu = 0.0, Q_VPR = 0.0;
    double Z_projected = 0.0;
    double vpr_correction = 0.0;
    int counter_valid = 0, counter_invalid = 0;
    
    for (int x = 0; x < (int)vol->num_x; x++) {
        for (int y = 0; y < (int)vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;
            
            // Use linear space for averaging (as per paper)
            double sum_Z_linear = 0.0;
            double sum_weights = 0.0;
            int found = 0;
            
            for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
                double estim_pia = vol->grid_att[idx];
                double atten_correction = 2 * estim_pia;
                if (atten_correction > 10) atten_correction = 10;
                
                double refl = vol->grid_refl[idx] + atten_correction;
                double height = vol->grid_height[idx];
                
                if (!isnan(refl)) {
                    // Calculate quality metrics
                    double height_km = height * 0.001;
                    Q_height = height_quality_metric_KNMI(height_km, 0.5, 1.0, 4.0);
                    Q_attenu = quality_reduction_KNMI(atten_correction, 3);
                    
                    // Force Q_height to [0,1]
                    if (Q_height > 1.0) Q_height = 1.0;
                    if (Q_height < 0.0) Q_height = 0.0;
                    
                    // Calculate VPR correction based on rain type
                    if (vol->grid_rain_type[idx] == 1) {
                        vpr_correction = compute_ground_to_altitude_diff(vpr_strat, height);
                        Z_projected = refl + vpr_correction;
                        Q_VPR = quality_reduction_KNMI(fabs(vpr_correction), 3);
                    } else if (vol->grid_rain_type[idx] == 2) {
                        vpr_correction = compute_ground_to_altitude_diff(vpr_conv, height);
                        Z_projected = refl + vpr_correction;
                        Q_VPR = quality_reduction_KNMI(fabs(vpr_correction), 3);
                    } else {
                        // Rain type 0 or 9 - no convection, no VPR correction needed
                   continue 
		    }
                    
                    // CRITICAL: Skip measurements with extremely poor VPR quality
                    if (Q_VPR < 1e-8) {
                        continue;  // This measurement is useless
                    }
                    
                    // Convert dBZ to linear (mm^6/m^3) - as per paper Eq. 1
                    double Z_linear = pow(10.0, Z_projected / 10.0);
                    
                    // Combined quality weight
                    double Q_T = Q_attenu * Q_height * Q_VPR;
                    
                    // Only include if weight is reasonable
                    if (Q_T > 1e-9 && Z_projected > -20.0 && Z_projected < 100.0) {
                        sum_Z_linear += Z_linear * Q_T;
                        sum_weights += Q_T;
                        found++;
                    }
                    
                    // Reset
                    Z_projected = 0.0;
                    Q_attenu = 0.0;
                    Q_height = 0.0;
                    Q_VPR = 0.0;
                }
            }
            
            // Compute final display value 
            if (found > 0 && sum_weights > 1e-12) {
                double Z_linear_avg = sum_Z_linear / sum_weights;
                
                // Convert back to dBZ
                double display_value = 10.0 * log10(Z_linear_avg);
                
                // Apply reasonable bounds for weather radar
                if (display_value < -10.0) display_value = -10.0;  // Noise floor
                if (display_value > 80.0) display_value = 80.0;    // Max reasonable
                
                vol->display_grid[base_idx] = display_value;
                
                // Debug output (only occasionally)
                if (base_idx % 50000 == 0 && found > 0) {
                    printf("Pixel (%d,%d): Z_lin=%.3e, Z_dB=%.2f (n=%d, sum_w=%.3e)\n", 
                           x, y, Z_linear_avg, display_value, found, sum_weights);
                }
            } else {
                // No valid data
                vol->display_grid[base_idx] = -32.0;  // Typical noise floor
            }
        }
    }
    
    printf("proportion of core / raincell = %.2f\n\n", 
           (double)counter_invalid / (double)(counter_valid + counter_invalid + 1));
    return 0;
}

*/


int compute_display_grid_KNMI(Vol_scan *vol, double threshold, const VPR *vpr_strat, const VPR *vpr_conv) {
    if (!vol) return -1;
    
    for (int x = 0; x < (int)vol->num_x; x++) {
        for (int y = 0; y < (int)vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;
            
            // First pass: collect all valid measurements for this pixel
            typedef struct {
                double Z_linear;
                double Q_raw;
            } Measurement;
            
            Measurement measurements[32];  // Max PPIs
            int n_meas = 0;
            double sum_raw_weights = 0.0;
            
            // Collect all measurements
            for (int ppi = 0; ppi < vol->num_PPIs && ppi < 32; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
                double estim_pia = vol->grid_att[idx];
                double atten_correction = 2 * estim_pia;
                if (atten_correction > 10) atten_correction = 10;
                
                double refl = vol->grid_refl[idx] + atten_correction;
                double height = vol->grid_height[idx];
                
                if (!isnan(refl) && refl > -30.0) {  // Valid reflectivity
                    // Calculate quality metrics
                    double Q_height = height_quality_metric_KNMI(height*0.001, 0.5, 1.0, 4.0);
                    double Q_attenu = quality_reduction_KNMI(atten_correction, 3);
                    
                    if (Q_height > 1.0) Q_height = 1.0;
                    if (Q_height < 0.0) Q_height = 0.0;
                    
                    double vpr_correction = 0.0;
                    double Q_VPR = 1.0;
                    
                    if (vol->grid_rain_type[idx] == 1) {
                        vpr_correction = compute_ground_to_altitude_diff(vpr_strat, height);
                        // Cap VPR correction
                        if (vpr_correction > 6.0) vpr_correction = 6.0;
                        if (vpr_correction < -6.0) vpr_correction = -6.0;
                        Q_VPR = quality_reduction_KNMI(fabs(vpr_correction), 3);
                    } else if (vol->grid_rain_type[idx] == 2) {
                        vpr_correction = compute_ground_to_altitude_diff(vpr_conv, height);
                        if (vpr_correction > 6.0) vpr_correction = 6.0;
                        if (vpr_correction < -6.0) vpr_correction = -6.0;
                        Q_VPR = quality_reduction_KNMI(fabs(vpr_correction), 3);
                    }
                    
                    double Z_projected = refl + vpr_correction;
                    double Z_linear = pow(10.0, Z_projected / 10.0);
                    double Q_raw = Q_attenu * Q_height * Q_VPR;
                    
                    // Only keep measurements with reasonable quality
                    if (Q_raw > 1e-6) {
                        measurements[n_meas].Z_linear = Z_linear;
                        measurements[n_meas].Q_raw = Q_raw;
                        sum_raw_weights += Q_raw;
                        n_meas++;
                    }
                }
            }
            
            // Second pass: compute weighted average with normalized weights
            if (n_meas > 0 && sum_raw_weights > 0) {
                double sum_Z_normalized = 0.0;
                
                for (int i = 0; i < n_meas; i++) {
                    double weight_normalized = measurements[i].Q_raw / sum_raw_weights;
                    sum_Z_normalized += measurements[i].Z_linear * weight_normalized;
                }
                
                // Convert to dBZ
                double Z_dB = 10.0 * log10(sum_Z_normalized);
                
                // Apply reasonable bounds
                if (Z_dB < -10.0) Z_dB = -10.0;
                if (Z_dB > 80.0) Z_dB = 80.0;
                
                vol->display_grid[base_idx] = Z_dB;
                
                // Debug
                if (base_idx % 100000 == 0) {
                    printf("Pixel (%d,%d): n_meas=%d, sum_weights=%.3f, Z_dB=%.2f\n", 
                           x, y, n_meas, sum_raw_weights, Z_dB);
                }
            } else {
                vol->display_grid[base_idx] = 0.00;  // No data
            }
        }
    }
    return 0;
}



double compute_ground_to_altitude_ratio(const VPR *vpr, double height){
	double Z_ground = get_reflectivity_at_height(vpr, vpr->GT.height);
	double Z_altitude = get_reflectivity_at_height(vpr, height);
	return Z_ground/Z_altitude;
}

double compute_ground_to_altitude_diff(const VPR *vpr, double height){
	double Z_ground = get_reflectivity_at_height(vpr, vpr->GT.height);
	double Z_altitude = get_reflectivity_at_height(vpr, height);
	return Z_ground - Z_altitude;
	//return Z_altitude - Z_ground;
}


double sigmoid_three_point(double p1, double p2, double p3){
	double prefactor = 2*log10(19);
	double exponent = prefactor*(p1-0.5*(p2+p3))/(p2-p3);
	return 1/(1+exp(exponent));
}

double height_quality_metric_KNMI(double height, double h_l, double h_m, double h_h){
	double quotient = 1/0.95;
	double numerator = sigmoid_three_point(height, 0, h_l)-0.05;
	double multiplier = sigmoid_three_point(height, h_h, h_m);
	return quotient*numerator*multiplier;
}	

double quality_reduction_KNMI(double x, double x_0){
	if(x == NAN){return 0.0;}
	return exp(-log(2)*(fabs(x)/x_0)*(fabs(x)/x_0));
}

int compute_display_grid_average(Vol_scan *vol, double threshold) {
    if (!vol) return -1;
        for (int x = 0; x < (int)vol->num_x; x++) {
    for (int y = 0; y < (int)vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;  // index into display_grid	
	    double dummy=0;
            int found = 0;

            for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
                double refl = vol->grid_refl[idx];
                if (!isnan(refl)) {
                        dummy = dummy + refl;
                        found = found + 1;
                }
            }
vol->display_grid[base_idx] = (dummy/(double)found < threshold) ? NAN : dummy/(double)found;
        }
    }

    return 0;
}

int compute_display_grid_max(Vol_scan *vol, double threshold) {
    if (!vol) return -1;

        for (int x = 0; x < (int)vol->num_x; x++) {
    for (int y = 0; y < (int)vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;  // index into display_grid
            double max_val = -INFINITY;
            int found = 0;

            for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
                double refl = vol->grid_refl[idx];
                if (!isnan(refl)) {
                    if (!found || refl > max_val) {
                        max_val = refl;
                        found = 1;
                    }
                }
            }
vol->display_grid[base_idx] = (!found || max_val < threshold) ? NAN : max_val;
        }
    }

    return 0;
}


int compute_display_grid_lowest_valid_height(Vol_scan *vol, double threshold) {
    if (!vol || !vol->grid_refl || !vol->display_grid || !vol->grid_height) return -1;
    // Debug: check grid_refl values
    int total_refl = 0;
    int refl_above_threshold = 0;
    for (size_t i = 0; i < vol->num_x * vol->num_y * vol->num_PPIs; i++) {
        if (!isnan(vol->grid_refl[i])) {
            total_refl++;
            if (vol->grid_refl[i] >= threshold) refl_above_threshold++;
        }
    }
    printf("DEBUG: grid_refl has %d valid values, %d above threshold %.1f\n", 
           total_refl, refl_above_threshold, threshold);
    
    for (size_t x = 0; x < vol->num_x; x++) {
        for (size_t y = 0; y < vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;  // index into display_grid
            double refl = NAN;
            double min_height = INFINITY;

            for (int ppi = 0; ppi < vol->num_PPIs; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
                double val = vol->grid_refl[idx];
                double hgt = vol->grid_height[idx];

                if (!isnan(val) && val >= threshold && hgt < min_height) {
                    refl = val;
                    min_height = hgt;
                }
            }

            vol->display_grid[base_idx] = refl;
        }
    }

    return 0;
}





int write_display_grid_to_file(const Vol_scan *vol, const char *filename) {
    if (!vol || !filename) return -1;

    FILE *f = fopen(filename, "w");
    if (!f) return -2;

    fprintf(f, "# Vol_scan Display Grid (max reflectivity across PPIs)\n");
    fprintf(f, "# Grid size: %zu x %zu\n", vol->num_x, vol->num_y);
    fprintf(f, "# Format: reflectivity\n");

    for (int x = 0; x < (int)vol->num_x; x++) {
        for (int y = 0; y < (int)vol->num_y; y++) {
            int idx = x * vol->num_y + y;
            double val = vol->display_grid[idx];
            if (isnan(val)) fprintf(f, "NaN ");
            else fprintf(f, "%.3f ", val);
        }
        fprintf(f, "\n");
    }

    fclose(f);
    return 0;
}
int write_true_grid_to_file(const Vol_scan *vol, const char *filename) {
    if (!vol || !filename) return -1;

    FILE *f = fopen(filename, "w");
    if (!f) return -2;

    fprintf(f, "# Vol_scan True Grid (RALA)\n");
    fprintf(f, "# Grid size: %zu x %zu\n", vol->num_x, vol->num_y);
    fprintf(f, "# Format: reflectivity\n");

    for (int x = 0; x < (int)vol->num_x; x++) {
        for (int y = 0; y < (int)vol->num_y; y++) {
            int idx = x * vol->num_y + y;
            double val = vol->refl_ALA[idx];
            if (isnan(val)) fprintf(f, "NaN ");
            else fprintf(f, "%.2f ", val);
        }
        fprintf(f, "\n");
    }

    fclose(f);
    return 0;
}
// A helper function to classify a point relative to a raincell
int classify_point_in_raincell(const Point *pt, const Point *raincell_center, const Raincell *raincell) {
    double dx = pt->x - raincell_center->x;
    double dy = pt->y - raincell_center->y;

    double distance_to_center = sqrt(dx*dx + dy*dy);

    // Compute distance to core using offset center
    double core_center_x = raincell_center->x - raincell->offset_centre_core;
    double core_center_y = raincell_center->y; // adjust if your core offset has y component
    double dx_core = pt->x - core_center_x;
    double dy_core = pt->y - core_center_y;
    double distance_to_core = sqrt(dx_core*dx_core + dy_core*dy_core);



    if (distance_to_center > raincell->radius_stratiform) {
        return 0; // outside
    } else if (distance_to_core <= raincell->radius_core) {
        return 2; // core
    } else {
        return 1; // stratiform
    }
}
int fill_refl_ALA_grid(Vol_scan *vol,
                       const Point *raincell_center,
                       const Raincell *raincell,
                       const VPR *vpr_1,
                       const VPR *vpr_2)
{
    if (!vol) {
        fprintf(stderr, "fill_refl_ALA_grid: NULL volume\n");
        return -1;
    }

    if (!raincell_center) {
        fprintf(stderr, "fill_refl_ALA_grid: NULL raincell_center pointer\n");
        return -2;
    }

    if (!raincell) {
        fprintf(stderr, "fill_refl_ALA_grid: NULL raincell struct\n");
        return -3;
    }

    if (!vpr_1 || !vpr_2) {
        fprintf(stderr, "fill_refl_ALA_grid: NULL VPR profile(s)\n");
        return -4;
    }

    // Allocate memory for refl_ALA if not already done
    if (!vol->refl_ALA) {
        size_t n = (size_t)vol->num_x * (size_t)vol->num_y;
        vol->refl_ALA = (double*)malloc(n * sizeof(double));
        if (!vol->refl_ALA) {
            perror("Failed to allocate memory for Refl_ALA");
            return -5;
        }
    }

    // DEBUG sanity check: print raincell position
    //fprintf(stderr, "Raincell center at x=%.2f, y=%.2f\n",
    //        raincell_center->x, raincell_center->y);

    // Fill grid
    for (int x = 0; x < (int)vol->num_x; x++) {
        for (int y = 0; y < (int)vol->num_y; y++) {
            int idx = x * vol->num_y + y;

            Point pt;
            pt.x = vol->ref_point.x + x * vol->resolution;
            pt.y = vol->ref_point.y + y * vol->resolution;

            int cls = classify_point_in_raincell(&pt, raincell_center, raincell);

            if (cls == 0) {
                vol->refl_ALA[idx] = NAN;
            } else if (cls == 1) {
                vol->refl_ALA[idx] = vpr_1->GT.reflectivity;
            } else if (cls == 2) {
                vol->refl_ALA[idx] = vpr_2->GT.reflectivity;
            } else {
                vol->refl_ALA[idx] = NAN; // unexpected classification
            }
        }
    }

    return 0;
}





void free_cart_grid(Cart_grid *cg) {
    if (!cg) return;
    free(cg->grid);
    free(cg->rain_type_grid);
    free(cg->height_grid);
    free(cg->estimated_attenuation_grid);
    free(cg);
}

static inline double dBZ_to_R(double dBZ) {
	double Z = pow(10.0, dBZ / 10.0);
    return pow(Z / 200.0, 1.0 / 1.6);
}
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
                                double *total_true_mm2_unmasked,
				double *total_unmasked_area_km2) // <-- Add this parameter)
{
    if (!vol || !vol->display_grid || !vol->refl_ALA) return -1;

    double sum_sq = 0.0, sum_abs = 0.0, sum_bias = 0.0;
    double sum_measured = 0.0, sum_true_masked = 0.0;
    double sum_measured_mm2_ = 0.0, sum_true_mm2_ = 0.0;

    double sum_true_all = 0.0;      // unmasked
    double sum_true_mm2_all = 0.0;  // unmasked
    int count = 0, count_all = 0;

    double cell_area_km2 = cart_grid_res*0.001 * cart_grid_res*0.001;
    double unmasked_area_accum = 0.0; // <-- Track active area
    for (int i = 0; i < (int)vol->num_elements; ++i) {
        double dBZ_disp = vol->display_grid[i];
        double dBZ_true = vol->refl_ALA[i];

        // --- Unmasked totals: include all valid refl_ALA ---
        if (!isnan(dBZ_true)) {
            double Rtrue = dBZ_to_R(dBZ_true);
            sum_true_all += Rtrue;
            sum_true_mm2_all += Rtrue * cell_area_km2;
            count_all++;
	    unmasked_area_accum += cell_area_km2; // <-- Accumulate area
        }

        // --- Masked stats for error metrics ---
        if (isnan(dBZ_disp) || isnan(dBZ_true)) continue;
        if (dBZ_disp < threshold) continue;

        double Rdisp = dBZ_to_R(dBZ_disp);
        double Rtrue = dBZ_to_R(dBZ_true);

        double err = Rdisp - Rtrue;

        sum_sq   += err * err;
        sum_abs  += fabs(err);
        sum_bias += err;

        sum_measured += Rdisp;
        sum_true_masked += Rtrue;

        sum_measured_mm2_ += Rdisp * cell_area_km2;
        sum_true_mm2_     += Rtrue * cell_area_km2;

        count++;
    }

    if (count == 0 || count_all == 0) return -1;

    *mse = sum_sq / count;
    *mae = sum_abs / count;
    *bias = sum_bias / count;

    *total_measured = sum_measured;
    *total_true_masked = sum_true_masked;
    *total_measured_mm2 = sum_measured_mm2_;
    *total_true_mm2 = sum_true_mm2_;

    *total_true_unmasked = sum_true_all;
    *total_true_mm2_unmasked = sum_true_mm2_all;
*total_unmasked_area_km2 = unmasked_area_accum; // <-- Pass it out
    return 0;
}


/**
 * @brief Save volume scan data to a binary file for Python visualization
 * @param vol Volume scan structure
 * @param filename Output filename
 * @return 0 on success, negative on error
 */
int save_vol_scan_to_file(Vol_scan *vol, const char *filename) {
    if (!vol || !filename) return -1;

    FILE *fp = fopen(filename, "wb");
    if (!fp) {
        perror("Failed to open file for writing");
        return -2;
    }

    // Write header information
    // Format: num_PPIs, num_x, num_y, resolution, ref_point.x, ref_point.y, ref_point.z
    int header[4] = {vol->num_PPIs, (int)vol->num_x, (int)vol->num_y};
    fwrite(header, sizeof(int), 3, fp);

    double params[4] = {vol->resolution, vol->ref_point.x, vol->ref_point.y, vol->ref_point.z};
    fwrite(params, sizeof(double), 4, fp);

    // Write the data arrays
    size_t ppi_size = vol->num_elements;
    size_t total_size = ppi_size * vol->num_PPIs;

    // Write reflectivity grid
    fwrite(vol->grid_refl, sizeof(double), total_size, fp);

    // Write height grid
    fwrite(vol->grid_height, sizeof(double), total_size, fp);

    // Write attenuation grid
    fwrite(vol->grid_att, sizeof(double), total_size, fp);

    // Write display grid (projected data)
    fwrite(vol->display_grid, sizeof(double), ppi_size, fp);

    // Write reflectivity at lowest altitude
    fwrite(vol->refl_ALA, sizeof(double), ppi_size, fp);

    fclose(fp);
    printf("Volume scan saved to %s\n", filename);
    return 0;
}

/**
 * @brief Save volume scan as text file (easier debugging, but larger)
 */
int save_vol_scan_to_text(Vol_scan *vol, const char *filename) {
    if (!vol || !filename) return -1;

    FILE *fp = fopen(filename, "w");
    if (!fp) {
        perror("Failed to open file for writing");
        return -2;
    }

    // Write metadata
    fprintf(fp, "# Volume Scan Data\n");
    fprintf(fp, "# Format: x y z reflectivity height attenuation\n");
    fprintf(fp, "# num_PPIs: %d\n", vol->num_PPIs);
    fprintf(fp, "# num_x: %zu\n", vol->num_x);
    fprintf(fp, "# num_y: %zu\n", vol->num_y);
    fprintf(fp, "# resolution: %f\n", vol->resolution);
    fprintf(fp, "# ref_point: (%f, %f, %f)\n",
            vol->ref_point.x, vol->ref_point.y, vol->ref_point.z);
    fprintf(fp, "\n");

    // Write data points
    for (int ppi_idx = 0; ppi_idx < vol->num_PPIs; ppi_idx++) {
        double z = vol->ref_point.z + ppi_idx * vol->resolution; // Assuming constant vertical spacing

        for (size_t y = 0; y < vol->num_y; y++) {
            for (size_t x = 0; x < vol->num_x; x++) {
                size_t idx = ppi_idx * vol->num_elements + y * vol->num_x + x;
                double px = vol->ref_point.x + x * vol->resolution;
                double py = vol->ref_point.y + y * vol->resolution;

                fprintf(fp, "%f %f %f %f %f %f\n",
                        px, py, z,
                        vol->grid_refl[idx],
                        vol->grid_height[idx],
                        vol->grid_att[idx]);
            }
        }
    }

    fclose(fp);
    return 0;
}






/**
 * @brief Processes each point in the volume scan, sorting reflectivity and attenuation
 *        into stratiform (type 1) and convective (type 2) VPR bins.
 * 
 * @param vs Pointer to the Vol_scan structure to process
 */
void process_volume_scan_VPR(Vol_scan *vs) {
    if (vs == NULL) return;
    
    // Initialize the empirical VPR arrays
    // First 40 entries (0-39): point counts per bin
    // Last 40 entries (40-79): cumulative reflectivity values
    memset(vs->emp_vpr_strat, 0, sizeof(vs->emp_vpr_strat));
    memset(vs->emp_vpr_conv, 0, sizeof(vs->emp_vpr_conv));
    
    // Constants
    const double MIN_HEIGHT = 0;      // m
    const double MAX_HEIGHT = 20000;     // m
    const double BIN_SIZE = 500;        // m
    const int NUM_BINS = 40;
    
    // Iterate through each PPI in the volume scan
    for (int ppi_idx = 0; ppi_idx < vs->num_PPIs; ppi_idx++) {
        
        // Iterate through x-dimension
        for (size_t x = 0; x < vs->num_x; x++) {
            
            // Iterate through y-dimension
            for (size_t y = 0; y < vs->num_y; y++) {
                
                // Calculate global index using the provided indexing function
                int global_idx = vol_index(vs, x, y, ppi_idx);
                
                // Get the rain type for this point
                int rain_type = vs->grid_rain_type[global_idx];
                
                // Skip if rain_type is not 1 or 2 (assuming 0 or negative indicate no data/invalid)
                if (rain_type != 1 && rain_type != 2) {
                    continue;
                }
                
                // Get the height for this point (in m)
                double height_m = vs->grid_height[global_idx];
                
                // Check if height is within valid range
                if (height_m < MIN_HEIGHT || height_m > MAX_HEIGHT) {
                    continue;
                }
                
                // Determine which bin this height falls into (0-39)
                int bin_index = (int)(height_m / BIN_SIZE);
                
                // Ensure bin_index is within valid range
                if (bin_index < 0 || bin_index >= NUM_BINS) {
                    continue;
                }
                
                // Get reflectivity value
                double reflectivity = vs->grid_refl[global_idx];
                
                // Get path-integrated attenuation and double it
                double atten = vs->grid_att[global_idx];
                double doubled_atten = 2.0 * atten;
		if(doubled_atten>10.0) doubled_atten = 10.0;

                // Calculate effective reflectivity: reflectivity + 2*attenuation
                double effective_refl = reflectivity + doubled_atten;
                
                // Store in appropriate VPR array based on rain type
                double *emp_vpr = (rain_type == 1) ? vs->emp_vpr_strat : vs->emp_vpr_conv;
                
                // Increment point count for this bin (indices 0-39)
                emp_vpr[bin_index] += 1.0;
                
                // Add to cumulative reflectivity (indices 40-79, offset by NUM_BINS)
                emp_vpr[NUM_BINS + bin_index] += effective_refl;
            }
        }
    }
}

/**
 * @brief Computes the average reflectivity for each VPR bin.
 * 
 * @param vs Pointer to the Vol_scan structure (must have been processed by process_volume_scan_VPR)
 */
void compute_average_empVPR(Vol_scan *vs) {
    if (vs == NULL) return;
    
    const int NUM_BINS = 40;
    
    // Process stratiform VPR (type 1)
    for (int bin = 0; bin < NUM_BINS; bin++) {
        double point_count = vs->emp_vpr_strat[bin];
        
        if (point_count > 0) {
            // Convert cumulative reflectivity to average
            vs->emp_vpr_strat[NUM_BINS + bin] /= point_count;
        }
        // If point_count is 0, leave the cumulative reflectivity as 0
        // (you could also set to NaN if desired: vs->emp_vpr_strat[NUM_BINS + bin] = NAN;)
    }
    
    // Process convective VPR (type 2)
    for (int bin = 0; bin < NUM_BINS; bin++) {
        double point_count = vs->emp_vpr_conv[bin];
        
        if (point_count > 0) {
            // Convert cumulative reflectivity to average
            vs->emp_vpr_conv[NUM_BINS + bin] /= point_count;
        }
    }
}



/**
 * @brief Computes the standard deviation for each VPR bin by making a second pass through the volume scan.
 *        Uses the previously computed average reflectivity for each bin.
 * 
 * @param vs Pointer to the Vol_scan structure (must have been processed by process_volume_scan_VPR and compute_average_empVPR)
 */
void compute_std_dev_empVPR(Vol_scan *vs) {
    if (vs == NULL) return;
    
    const int NUM_BINS = 40;
    const double MIN_HEIGHT = 0;      // m
    const double MAX_HEIGHT = 20000;  // m
    const double BIN_SIZE = 500;      // m
    
    // First, initialize the sum of squared differences to zero
    // Indices 80-119 will store the sum of squared differences
    for (int bin = 0; bin < NUM_BINS; bin++) {
        vs->emp_vpr_strat[2 * NUM_BINS + bin] = 0.0;
        vs->emp_vpr_conv[2 * NUM_BINS + bin] = 0.0;
    }
    
    // Second pass: iterate through all points to calculate sum of squared differences
    for (int ppi_idx = 0; ppi_idx < vs->num_PPIs; ppi_idx++) {
        for (size_t x = 0; x < vs->num_x; x++) {
            for (size_t y = 0; y < vs->num_y; y++) {
                int global_idx = vol_index(vs, x, y, ppi_idx);
                
                int rain_type = vs->grid_rain_type[global_idx];
                if (rain_type != 1 && rain_type != 2) continue;
                
                double height_m = vs->grid_height[global_idx];
                if (height_m < MIN_HEIGHT || height_m > MAX_HEIGHT) continue;
                
                int bin_index = (int)(height_m / BIN_SIZE);
                if (bin_index < 0 || bin_index >= NUM_BINS) continue;
                
                double reflectivity = vs->grid_refl[global_idx];
                double atten = vs->grid_att[global_idx];
                double doubled_atten = 2.0 * atten;
                if (doubled_atten > 10.0) doubled_atten = 10.0;
                
                double effective_refl = reflectivity + doubled_atten;
                
                // Get the average for this bin
                double avg_refl = 0.0;
                double *sum_sq_diff = NULL;
                
                if (rain_type == 1) {
                    avg_refl = vs->emp_vpr_strat[NUM_BINS + bin_index];
                    sum_sq_diff = &vs->emp_vpr_strat[2 * NUM_BINS + bin_index];
                } else {
                    avg_refl = vs->emp_vpr_conv[NUM_BINS + bin_index];
                    sum_sq_diff = &vs->emp_vpr_conv[2 * NUM_BINS + bin_index];
                }
                
                // Accumulate sum of squared differences
                double diff = effective_refl - avg_refl;
                *sum_sq_diff += (diff * diff);
            }
        }
    }
    
    // Now calculate the standard deviation for each bin
    // Process stratiform VPR (type 1)
    for (int bin = 0; bin < NUM_BINS; bin++) {
        double point_count = vs->emp_vpr_strat[bin];
        double sum_sq_diff = vs->emp_vpr_strat[2 * NUM_BINS + bin];
        
        if (point_count > 1) {
            // Sample standard deviation: sqrt( sum((x - mean)²) / (n-1) )
            double variance = sum_sq_diff / (point_count - 1.0);
            vs->emp_vpr_strat[2 * NUM_BINS + bin] = (1/point_count)*sqrt(variance);
        } else if (point_count == 1) {
            vs->emp_vpr_strat[2 * NUM_BINS + bin] = 0.0;
        } else {
            vs->emp_vpr_strat[2 * NUM_BINS + bin] = 0.0;  // No data
        }
    }
    
    // Process convective VPR (type 2)
    for (int bin = 0; bin < NUM_BINS; bin++) {
        double point_count = vs->emp_vpr_conv[bin];
        double sum_sq_diff = vs->emp_vpr_conv[2 * NUM_BINS + bin];
        
        if (point_count > 1) {
            double variance = sum_sq_diff / (point_count - 1.0);
            vs->emp_vpr_conv[2 * NUM_BINS + bin] =  (1/point_count)*sqrt(variance);
        } else if (point_count == 1) {
            vs->emp_vpr_conv[2 * NUM_BINS + bin] = 0.0;
        } else {
            vs->emp_vpr_conv[2 * NUM_BINS + bin] = 0.0;  // No data
        }
    }
}


/**
 * @brief Prints the empirical vertical profiles to a file.
 *        Writes one profile per line (40 points per profile).
 *        Each subsequent call appends a new profile on a new line.
 * 
 * @param vs Pointer to the Vol_scan structure containing the VPR data
 * @param filename Name of the file to write to
 * @param profile_type Type of profile to print: 
 *                     1 for stratiform, 2 for convective
 * @return 0 on success, -1 on error
 */
int print_vpr_profile(const Vol_scan *vs, const char *filename, int profile_type) {
    if (vs == NULL || filename == NULL) {
        return -1;
    }
    
    const int NUM_BINS = 40;
    double *emp_vpr = NULL;
    const char *profile_name = NULL;
    
    // Select the appropriate profile
    if (profile_type == 1) {
        emp_vpr = vs->emp_vpr_strat;
        profile_name = "stratiform";
    } else if (profile_type == 2) {
        emp_vpr = vs->emp_vpr_conv;
        profile_name = "convective";
    } else {
        fprintf(stderr, "Error: Invalid profile_type. Use 1 for stratiform, 2 for convective.\n");
        return -1;
    }
    
    // Open file in append mode to add new profiles at the end
    FILE *file = fopen(filename, "a");
    if (file == NULL) {
        fprintf(stderr, "Error: Could not open file '%s' for writing.\n", filename);
        return -1;
    }
    
    // Write the profile type as a comment or identifier (optional)
    // fprintf(file, "# %s profile\n", profile_name);
    
    // Write the 40 average reflectivity values (indices 40-79) on one line
    for (int bin = 0; bin < NUM_BINS; bin++) {
        fprintf(file, "%.6f", emp_vpr[NUM_BINS + bin]);
        
        // Add space between values, but not after the last one
        if (bin < NUM_BINS - 1) {
            fprintf(file, " ");
        }
    }
    
    // Add newline to separate profiles
    fprintf(file, "\n");
    
    // Close the file
    fclose(file);
    
    return 0;
}
/**
 * @brief Prints the complete VPR data (both point counts and averages) to a file.
 *        Format: For each bin: bin_center_height count avg_reflectivity
 * 
 * @param vs Pointer to the Vol_scan structure
 * @param filename Name of the file to write to
 * @param profile_type 1 for stratiform, 2 for convective
 * @param append If non-zero, append to file; if 0, overwrite file
 * @return 0 on success, -1 on error
 */
int print_vpr_detailed(const Vol_scan *vs, const char *filename, int profile_type, int append) {
    if (vs == NULL || filename == NULL) {
        return -1;
    }
    
    const int NUM_BINS = 40;
    const double BIN_SIZE = 0.5;  // km
    const double BIN_CENTER_OFFSET = BIN_SIZE / 2.0;  // 0.25 km
    
    double *emp_vpr = NULL;
    const char *mode = append ? "a" : "w";
    const char *profile_name = (profile_type == 1) ? "stratiform" : "convective";
    
    // Select the appropriate profile
    if (profile_type == 1) {
        emp_vpr = vs->emp_vpr_strat;
    } else if (profile_type == 2) {
        emp_vpr = vs->emp_vpr_conv;
    } else {
        fprintf(stderr, "Error: Invalid profile_type. Use 1 for stratiform, 2 for convective.\n");
        return -1;
    }
    
    // Open file
    FILE *file = fopen(filename, mode);
    if (file == NULL) {
        fprintf(stderr, "Error: Could not open file '%s' for writing.\n", filename);
        return -1;
    }
    
    // Write header (only if not appending or file is new)
    if (!append || ftell(file) == 0) {
        fprintf(file, "# %s Vertical Profile Reflectivity (VPR)\n", profile_name);
        fprintf(file, "# Format: bin_index bin_center_height_km point_count avg_reflectivity_dBZ\n");
        fprintf(file, "# Height bins: 0-20 km in 0.5 km increments\n");
        fprintf(file, "# Bins 0-39: %s\n", (profile_type == 1) ? "stratiform" : "convective");
        fprintf(file, "#\n");
    }
    
    // Write data for each bin
    for (int bin = 0; bin < NUM_BINS; bin++) {
        double bin_center = bin * BIN_SIZE + BIN_CENTER_OFFSET;
        double point_count = emp_vpr[bin];
        double avg_reflectivity = emp_vpr[NUM_BINS + bin];
        
        // Only write bins that have data (optional)
        // if (point_count > 0) {
            fprintf(file, "%d %.2f %.0f %.6f\n", bin, bin_center, point_count, avg_reflectivity);
        // }
    }
    
    fprintf(file, "\n");  // Add empty line between profiles if appending
    
    fclose(file);
    
    return 0;
}


int print_vpr_detailed_no_vol(const double vpr[120], const char *filename, int profile_type, int append) {

    const int NUM_BINS = 40;
    const double BIN_SIZE = 0.5;  // km
    const double BIN_CENTER_OFFSET = BIN_SIZE / 2.0;  // 0.25 km

    const char *mode = append ? "a" : "w";

    // Open file
    FILE *file = fopen(filename, mode);
    if (file == NULL) {
        fprintf(stderr, "Error: Could not open file '%s' for writing.\n", filename);
        return -1;
    }
	char p1[6] = "strat";
	char p2[6] = "conv";
	char *profile_name;
    if(profile_type == 1){
    profile_name = p1;
    }
if(profile_type == 2){
    profile_name = p2;
    }
    // Write header (only if not appending or file is new)
    if (!append || ftell(file) == 0) {
        fprintf(file, "# %s Vertical Profile Reflectivity (VPR) with Standard Deviation\n", profile_name);
        fprintf(file, "# Format: bin_index bin_center_height_km point_count avg_reflectivity_dBZ std_deviation_dBZ\n");
        fprintf(file, "# Height bins: 0-20 km in 0.5 km increments\n");
        fprintf(file, "# Bins 0-39: %s\n", (profile_type == 1) ? "stratiform" : "convective");
        fprintf(file, "# Standard deviation is sample standard deviation (dividing by n-1)\n");
        fprintf(file, "#\n");
    }

    // Write data for each bin
    for (int bin = 0; bin < NUM_BINS; bin++) {
        double bin_center = bin * BIN_SIZE + BIN_CENTER_OFFSET;
        double point_count = vpr[bin];
        double avg_reflectivity = vpr[NUM_BINS + bin];
        double std_deviation = vpr[2 * NUM_BINS + bin];

        // Check if standard deviation is valid (not NaN)
        if (isnan(std_deviation)) {
            fprintf(file, "%d %.2f %.0f %.6f %s\n", bin, bin_center, point_count, avg_reflectivity, "NaN");
        } else {
            fprintf(file, "%d %.2f %.0f %.6f %.6f\n", bin, bin_center, point_count, avg_reflectivity, std_deviation);
        }
    }

    fprintf(file, "\n");  // Add empty line between profiles if appending

    fclose(file);

    return 0;
}




double get_reflectivity_from_empirical_vpr_interp(const double *emp_vpr, double height, double bin_size_km, double ground_height_km) {
    const int NUM_BINS = 40;
    const double BIN_SIZE = bin_size_km*1000;
    const double HALF_BIN = BIN_SIZE / 2.0;
    
    // Calculate bin index and fractional position
    double bin_center = (int)(height / BIN_SIZE) * BIN_SIZE + HALF_BIN;
    int bin_index = (int)(height / BIN_SIZE);
    
    // Check bounds
    if (bin_index < 0 || bin_index >= NUM_BINS) {
        
//	printf("_1_");
	    return NAN;
    }
    
    // Get point counts for current and adjacent bins
    double count_current = emp_vpr[bin_index];
    double refl_current = emp_vpr[NUM_BINS + bin_index];
    
    // If current bin has data, we'll use it with possible interpolation
    if (count_current > 0) {
        // Check if we need to interpolate with adjacent bins
        double height_offset = height - bin_center;
        double interp_factor = height_offset / BIN_SIZE;
        
        // Try to interpolate with next bin if height is above bin center
        if (interp_factor > 0 && bin_index + 1 < NUM_BINS) {
            double count_next = emp_vpr[bin_index + 1];
            double refl_next = emp_vpr[NUM_BINS + bin_index + 1];
            
            if (count_next > 0) {
                // Linear interpolation between current and next bin
                double refl_interp = refl_current * (1.0 - interp_factor) + refl_next * interp_factor;
                return refl_interp;
            }
        }
        // Try to interpolate with previous bin if height is below bin center
        else if (interp_factor < 0 && bin_index - 1 >= 0) {
            double count_prev = emp_vpr[bin_index - 1];
            double refl_prev = emp_vpr[NUM_BINS + bin_index - 1];
            
            if (count_prev > 0) {
                // Linear interpolation between previous and current bin
                double refl_interp = refl_prev * (1.0 + interp_factor) + refl_current * (-interp_factor);
                return refl_interp;
            }
        }
        
        // No interpolation possible, return current bin value
        return refl_current;
    } else {
        // Current bin has no data, find nearest bin with data
        int nearest_bin = -1;
        double min_distance = 1e6;
        
        for (int i = 0; i < NUM_BINS; i++) {
            if (emp_vpr[i] > 0) {
                double bin_center_i = i * BIN_SIZE + HALF_BIN;
                double distance = fabs(bin_center_i - height);
                if (distance < min_distance) {
                    min_distance = distance;
                    nearest_bin = i;
                }
            }
        }
        
        if (nearest_bin >= 0) {
            return emp_vpr[NUM_BINS + nearest_bin];
        } else {
        
	printf("_2_");
	    	return NAN;
        }
    }
}


double get_stdev_from_empirical_vpr_interp(const double *emp_vpr, double height, double bin_size_km, double ground_height_km) {
    const int NUM_BINS = 40;
    const double BIN_SIZE = bin_size_km*1000;
    const double HALF_BIN = BIN_SIZE / 2.0;
    
    // Calculate bin index and fractional position
    double bin_center = (int)(height / BIN_SIZE) * BIN_SIZE + HALF_BIN;
    int bin_index = (int)(height / BIN_SIZE);
    
    // Check bounds
    if (bin_index < 0 || bin_index >= NUM_BINS) {
	//printf("_1_");
    	    return NAN;
    }
    
    // Get point counts for current and adjacent bins
    double count_current = emp_vpr[bin_index];
    double stdev_current = emp_vpr[2*NUM_BINS + bin_index];
    
    // If current bin has data, we'll use it with possible interpolation
    if (count_current > 0) {
        // Check if we need to interpolate with adjacent bins
        double height_offset = height - bin_center;
        double interp_factor = height_offset / BIN_SIZE;
        
        // Try to interpolate with next bin if height is above bin center
        if (interp_factor > 0 && bin_index + 1 < NUM_BINS) {
            double count_next = emp_vpr[bin_index + 1];
            double stdev_next = emp_vpr[2*NUM_BINS + bin_index + 1];
            
            if (count_next > 0) {
                // Linear interpolation between current and next bin
                double stdev_interp = stdev_current * (1.0 - interp_factor) + stdev_next * interp_factor;
                return stdev_interp;
            }
        }
        // Try to interpolate with previous bin if height is below bin center
        else if (interp_factor < 0 && bin_index - 1 >= 0) {
            double count_prev = emp_vpr[bin_index - 1];
            double stdev_prev = emp_vpr[2*NUM_BINS + bin_index - 1];
            
            if (count_prev > 0) {
                // Linear interpolation between previous and current bin
                double stdev_interp = stdev_prev * (1.0 + interp_factor) + stdev_current * (-interp_factor);
                return stdev_interp;
            }
        }
        
        // No interpolation possible, return current bin value
        return stdev_current;
    } else {
        // Current bin has no data, find nearest bin with data
        int nearest_bin = -1;
        double min_distance = 1e6;
        
        for (int i = 0; i < NUM_BINS; i++) {
            if (emp_vpr[i] > 0) {
                double bin_center_i = i * BIN_SIZE + HALF_BIN;
                double distance = fabs(bin_center_i - height);
                if (distance < min_distance) {
                    min_distance = distance;
                    nearest_bin = i;
                }
            }
        }
        
        if (nearest_bin >= 0) {
            return emp_vpr[2*NUM_BINS + nearest_bin];
        } else {

	//printf("_2_");
            return NAN;
        }
    }
}

// Updated function to compute ground-to-altitude difference using empirical VPR
double compute_ground_to_altitude_diff_empirical(const Vol_scan *vol, double height, int rain_type, 
                                                   double bin_size_km, double ground_height_km) {
    double Z_ground = NAN;
    double Z_altitude = NAN;
    
    // Select the appropriate empirical VPR based on rain type
    const double *emp_vpr = NULL;
    if (rain_type == 1) {
        emp_vpr = vol->emp_vpr_strat;
    } else if (rain_type == 2) {
        emp_vpr = vol->emp_vpr_conv;
    } else {
        return 0.0;  // Unknown rain type
    }
    
    // Get reflectivity at ground level (lowest altitude with data)
    // Find the lowest bin that has data
    const int NUM_BINS = 40;
    int lowest_bin = -1;
    for (int i = 0; i < NUM_BINS; i++) {
        if (emp_vpr[i] > 0) {
            lowest_bin = i;
            break;
        }
    }
    
    if (lowest_bin >= 0) {
        // Use the reflectivity from the lowest bin as ground reflectivity
        Z_ground = emp_vpr[NUM_BINS + lowest_bin];
        
        // Get reflectivity at the specified altitude
        Z_altitude = get_reflectivity_from_empirical_vpr_interp(emp_vpr, height, bin_size_km, ground_height_km);
      // printf("%.3e",Z_altitude); 
        if (!isnan(Z_ground) && !isnan(Z_altitude)) {
            return Z_ground - Z_altitude;
            //return Z_altitude-Z_ground;
        }
    }
    
    return 0.0;  // Default if no valid data
}


// Updated function to compute ground-to-altitude difference using empirical VPR
double compute_VPR_stdev_at_height_empirical(const Vol_scan *vol, double height, int rain_type, 
                                                   double bin_size_km, double ground_height_km) {
    double stdev_altitude = NAN;
    
    // Select the appropriate empirical VPR based on rain type
    const double *emp_vpr = NULL;
    if (rain_type == 1) {
        emp_vpr = vol->emp_vpr_strat;
    } else if (rain_type == 2) {
        emp_vpr = vol->emp_vpr_conv;
    } else {
        return 0.0;  // Unknown rain type
    }
    
    // Get reflectivity at ground level (lowest altitude with data)
    // Find the lowest bin that has data
    const int NUM_BINS = 40;
    int lowest_bin = -1;
    for (int i = 0; i < NUM_BINS; i++) {
        if (emp_vpr[i] > 0) {
            lowest_bin = i;
            break;
        }
    }
    
    if (lowest_bin >= 0) {
        // Get stdev at the specified altitude
        stdev_altitude = get_stdev_from_empirical_vpr_interp(emp_vpr, height, bin_size_km, ground_height_km);
      // printf("%.3e",Z_altitude); 
        if (!isnan(stdev_altitude)) {
            return stdev_altitude;
        }
    }
    
    return 0.0;  // Default if no valid data
}




// Updated main function that uses empirical VPR
int compute_display_grid_KNMI_empirical(Vol_scan *vol, double threshold, double bin_size_km, double ground_height_km) {
    if (!vol) return -1;
    
    const int NUM_BINS = 40;
int n_unc_eq_1 = 0;
int n_unc_lt_1e5 = 0;
double sum_unc_remaining = 0.0;
int n_unc_remaining = 0;
	
    for (int x = 0; x < (int)vol->num_x; x++) {
        for (int y = 0; y < (int)vol->num_y; y++) {
            int base_idx = x * vol->num_y + y;
            
            // First pass: collect all valid measurements for this pixel
            typedef struct {
                double Z_linear;
                double Q_raw;
            } Measurement;
            
            Measurement measurements[32];  // Max PPIs
            int n_meas = 0;
            double sum_raw_weights = 0.0;
      
			
			// Add these counters before the loop
	      
            // Collect all measurements
            for (int ppi = 0; ppi < vol->num_PPIs && ppi < 32; ppi++) {
                int idx = vol_index(vol, x, y, ppi);
                double estim_pia = vol->grid_att[idx];
                double atten_correction = 2 * estim_pia;
                //double atten_correction = 0.0;
                if (atten_correction > 10) atten_correction = 10;
                
                double refl = vol->grid_refl[idx] + atten_correction;
                double height = vol->grid_height[idx];
                
                if (!isnan(refl) && refl > -30.0) {  // Valid reflectivity
                    // Calculate quality metrics
                    double Q_height = height_quality_metric_KNMI(height*0.001, 0.5, 1.0, 4.0);
                    double Q_attenu = quality_reduction_KNMI(atten_correction, 3);
                    
                    if (Q_height > 1.0) Q_height = 1.0;
                    if (Q_height < 0.0) Q_height = 0.0;
                    
                    double vpr_correction = 0.0;
                    double Q_VPR = 1.0;
                    double Q_VPR_unc = 1.0;
                    // Use empirical VPR based on rain type
                    if (vol->grid_rain_type[idx] == 1 || vol->grid_rain_type[idx] == 2) {
                         vpr_correction = compute_ground_to_altitude_diff_empirical(vol, height, 
                                                                                    vol->grid_rain_type[idx],
                                                                                    bin_size_km, ground_height_km);
     
			 //printf("%.3d", vpr_correction);
                     
	 double stdev = compute_VPR_stdev_at_height_empirical(vol, height, 
                                                                                    vol->grid_rain_type[idx],
                                                                                    bin_size_km, ground_height_km);
     
				
				
				
				
                        
                        // Cap VPR correction
                        if (vpr_correction > 6.0) vpr_correction = 6.0;
                        if (vpr_correction < -6.0) vpr_correction = -6.0;
                        
                        // Quality based on absolute correction
                        Q_VPR = quality_reduction_KNMI(fabs(vpr_correction), 3);
      


		
			Q_VPR_unc = quality_reduction_KNMI(fabs(3*stdev),3); 
		//	printf("%.3e",Q_VPR_unc);
// Statistics collection
if (Q_VPR_unc == 1) {
    n_unc_eq_1++;
} else if (Q_VPR_unc < 1e-5) {
    n_unc_lt_1e5++;
} else {
    sum_unc_remaining += Q_VPR_unc;
    n_unc_remaining++;
}		    
		    }
                    
                    double Z_projected = refl + vpr_correction;
                    double Z_linear = pow(10.0, Z_projected / 10.0);
                    double Q_raw = Q_attenu * Q_height * Q_VPR * Q_VPR_unc;
                    
                    // Only keep measurements with reasonable quality
                    if (Q_raw > 1e-6) {
                        measurements[n_meas].Z_linear = Z_linear;
                        measurements[n_meas].Q_raw = Q_raw;
                        sum_raw_weights += Q_raw;
                        n_meas++;
                    }
                }
            }
            

            // Second pass: compute weighted average with normalized weights
            if (n_meas > 0 && sum_raw_weights > 0) {
                double sum_Z_normalized = 0.0;
                
                for (int i = 0; i < n_meas; i++) {
                    double weight_normalized = measurements[i].Q_raw / sum_raw_weights;
                    sum_Z_normalized += measurements[i].Z_linear * weight_normalized;
                }
                
                // Convert to dBZ
                double Z_dB = 10.0 * log10(sum_Z_normalized);
                
                // Apply reasonable bounds
                if (Z_dB < -10.0) Z_dB = -10.0;
                if (Z_dB > 80.0) Z_dB = 80.0;
                
                vol->display_grid[base_idx] = Z_dB;
                
                // Debug
                if (base_idx % 100000 == 0) {
                    printf("Pixel (%d,%d): n_meas=%d, sum_weights=%.3f, Z_dB=%.2f\n", 
                           x, y, n_meas, sum_raw_weights, Z_dB);
                }
            } else {
                vol->display_grid[base_idx] = 0.00;  // No data
            }
        }
    }
/*
// After the loop ends, print the statistics:
printf("\n=== Q_ Statistics ===\n");
printf("Number of Q_VPR == 1.0: %d\n", n_unc_eq_1);
printf("Number of Q_VPR < 1e-5: %d\n", n_unc_lt_1e5);
if (n_unc_remaining > 0) {
    printf("Average of remaining Q_VPR values: %.6f (based on %d values)\n", 
           sum_unc_remaining / n_unc_remaining, n_unc_remaining);
} else {
    printf("No remaining Q_VPR_unc values to average.\n");
}
printf("================================\n");
*/


    return 0;
}




/**
 * @brief Prints the complete VPR data (point counts, average reflectivity, and standard deviation) to a file.
 *        Format: For each bin: bin_index bin_center_height_km point_count avg_reflectivity_dBZ std_deviation_dBZ
 *
 * @param vs Pointer to the Vol_scan structure
 * @param filename Name of the file to write to
 * @param profile_type 1 for stratiform, 2 for convective
 * @param append If non-zero, append to file; if 0, overwrite file
 * @return 0 on success, -1 on error
 */
int print_vpr_detailed_with_std(const Vol_scan *vs, const char *filename, int profile_type, int append) {
    if (vs == NULL || filename == NULL) {
        return -1;
    }

    const int NUM_BINS = 40;
    const double BIN_SIZE = 0.5;  // km
    const double BIN_CENTER_OFFSET = BIN_SIZE / 2.0;  // 0.25 km

    double *emp_vpr = NULL;
    const char *mode = append ? "a" : "w";
    const char *profile_name = (profile_type == 1) ? "stratiform" : "convective";

    // Select the appropriate profile
    if (profile_type == 1) {
        emp_vpr = (double*)vs->emp_vpr_strat;
    } else if (profile_type == 2) {
        emp_vpr = (double*)vs->emp_vpr_conv;
    } else {
        fprintf(stderr, "Error: Invalid profile_type. Use 1 for stratiform, 2 for convective.\n");
        return -1;
    }

    // Open file
    FILE *file = fopen(filename, mode);
    if (file == NULL) {
        fprintf(stderr, "Error: Could not open file '%s' for writing.\n", filename);
        return -1;
    }

    // Write header (only if not appending or file is new)
    if (!append || ftell(file) == 0) {
        fprintf(file, "# %s Vertical Profile Reflectivity (VPR) with Standard Deviation\n", profile_name);
        fprintf(file, "# Format: bin_index bin_center_height_km point_count avg_reflectivity_dBZ std_deviation_dBZ\n");
        fprintf(file, "# Height bins: 0-20 km in 0.5 km increments\n");
        fprintf(file, "# Bins 0-39: %s\n", (profile_type == 1) ? "stratiform" : "convective");
        fprintf(file, "# Standard deviation is sample standard deviation (dividing by n-1)\n");
        fprintf(file, "#\n");
    }

    // Write data for each bin
    for (int bin = 0; bin < NUM_BINS; bin++) {
        double bin_center = bin * BIN_SIZE + BIN_CENTER_OFFSET;
        double point_count = emp_vpr[bin];
        double avg_reflectivity = emp_vpr[NUM_BINS + bin];
        double std_deviation = emp_vpr[2 * NUM_BINS + bin];

        // Check if standard deviation is valid (not NaN)
        if (isnan(std_deviation)) {
            fprintf(file, "%d %.2f %.0f %.6f %s\n", bin, bin_center, point_count, avg_reflectivity, "NaN");
        } else {
            fprintf(file, "%d %.2f %.0f %.6f %.6f\n", bin, bin_center, point_count, avg_reflectivity, std_deviation);
        }
    }

    fprintf(file, "\n");  // Add empty line between profiles if appending

    fclose(file);

    return 0;
}


/**
 * @brief Initializes VPR arrays for empirical VPR calculation from polar data
 */
void init_polar_vpr_arrays(double vpr_strat[120], double vpr_conv[120]) {
    for (int i = 0; i < 120; i++) {
        vpr_strat[i] = 0.0;
        vpr_conv[i] = 0.0;
    }
}

/**
 * @brief Processes a single Polar_box and accumulates reflectivity into VPR bins
 */
void process_polar_box_for_vpr(Polar_box *box, double vpr_strat[120], double vpr_conv[120]) {
    if (box == NULL) return;

    const int NUM_BINS = 40;
    const double MIN_HEIGHT = 0.0;
    const double MAX_HEIGHT = 20000.0;
    const double BIN_SIZE = 500.0;

    for (int r = 0; r < box->num_ranges; r++) {
        for (int a = 0; a < box->num_angles; a++) {
            int idx = a * box->num_ranges + r;

            int rain_type = box->rain_type[idx];
            if (rain_type != 1 && rain_type != 2) continue;

            double height_m = box->height_grid[idx];
            if (height_m < MIN_HEIGHT || height_m > MAX_HEIGHT) continue;

            int bin_index = (int)(height_m / BIN_SIZE);
            if (bin_index < 0 || bin_index >= NUM_BINS) continue;

            double reflectivity = box->grid[idx];
            double atten = box->estimated_attenuation_grid[idx];
            double doubled_atten = 2.0 * atten;
            if (doubled_atten > 10.0) doubled_atten = 10.0;

            double effective_refl = reflectivity + doubled_atten;

            double *vpr_array = (rain_type == 1) ? vpr_strat : vpr_conv;

            // Increment point count (indices 0-39)
            vpr_array[bin_index] += 1.0;

            // Add to cumulative reflectivity (indices 40-79)
            vpr_array[NUM_BINS + bin_index] += effective_refl;
        }
    }
}

/**
 * @brief Computes average reflectivity for each bin in-place (stores in indices 40-79)
 */
void compute_polar_vpr_averages_inplace(double vpr_array[120]) {
    const int NUM_BINS = 40;

    for (int bin = 0; bin < NUM_BINS; bin++) {
        double point_count = vpr_array[bin];

        if (point_count > 0) {
            vpr_array[NUM_BINS + bin] /= point_count;
        } else {
            vpr_array[NUM_BINS + bin] = 0.0;
        }
    }
}

/**
 * @brief Processes a single Polar_box for standard deviation (accumulates squared differences)
 */
void process_polar_box_for_std_dev(Polar_box *box, double vpr_array[120]) {
    if (box == NULL) return;

    const int NUM_BINS = 40;
    const double MIN_HEIGHT = 0.0;
    const double MAX_HEIGHT = 20000.0;
    const double BIN_SIZE = 500.0;

    for (int r = 0; r < box->num_ranges; r++) {
        for (int a = 0; a < box->num_angles; a++) {
            int idx = a * box->num_ranges + r;

            int rain_type = box->rain_type[idx];
            if (rain_type != 1 && rain_type != 2) continue;

            double height_m = box->height_grid[idx];
            if (height_m < MIN_HEIGHT || height_m > MAX_HEIGHT) continue;

            int bin_index = (int)(height_m / BIN_SIZE);
            if (bin_index < 0 || bin_index >= NUM_BINS) continue;

            double reflectivity = box->grid[idx];
            double atten = box->estimated_attenuation_grid[idx];
            double doubled_atten = 2.0 * atten;
            if (doubled_atten > 10.0) doubled_atten = 10.0;

            double effective_refl = reflectivity + doubled_atten;

            // Get the average for this bin (stored at index 40+bin_index)
            double avg_refl = vpr_array[NUM_BINS + bin_index];

            // Accumulate sum of squared differences (indices 80-119)
            double diff = effective_refl - avg_refl;
            vpr_array[2 * NUM_BINS + bin_index] += (diff * diff);
        }
    }
}

/**
 * @brief Computes standard deviation for each bin in-place (stores in indices 80-119)
 */
void compute_polar_vpr_std_dev_inplace(double vpr_array[120]) {
    const int NUM_BINS = 40;

    for (int bin = 0; bin < NUM_BINS; bin++) {
        double point_count = vpr_array[bin];
        double sum_sq_diff = vpr_array[2 * NUM_BINS + bin];

        if (point_count > 1) {
            double variance = sum_sq_diff / (point_count - 1.0);
            vpr_array[2 * NUM_BINS + bin] = (1/point_count)*sqrt(variance);
        } else {
            vpr_array[2 * NUM_BINS + bin] = 0.0;
        }
    }
}

// Add this function to create an adaptive volume scan using empirical VPRs
Vol_scan* create_adaptive_vol_scan(Vol_scan *original_vol, double *emp_vpr_strat, double *emp_vpr_conv) {
    if (!original_vol) return NULL;

    // Create a deep copy of the volume scan
    Vol_scan *ad_vol = malloc(sizeof(Vol_scan));
    if (!ad_vol) return NULL;

    // Copy basic properties
    ad_vol->num_PPIs = original_vol->num_PPIs;
    ad_vol->num_elements = original_vol->num_elements;
    ad_vol->num_x = original_vol->num_x;
    ad_vol->num_y = original_vol->num_y;
    ad_vol->ref_point = original_vol->ref_point;
    ad_vol->resolution = original_vol->resolution;

    // Allocate and copy arrays
    size_t total_elements = ad_vol->num_elements * ad_vol->num_PPIs;

    ad_vol->grid_refl = malloc(total_elements * sizeof(double));
    ad_vol->grid_height = malloc(total_elements * sizeof(double));
    ad_vol->grid_att = malloc(total_elements * sizeof(double));
    ad_vol->grid_rain_type = malloc(total_elements * sizeof(int));
    ad_vol->display_grid = malloc(ad_vol->num_elements * sizeof(double));
    ad_vol->refl_ALA = malloc(ad_vol->num_elements * sizeof(double));

    if (!ad_vol->grid_refl || !ad_vol->grid_height || !ad_vol->grid_att ||
        !ad_vol->grid_rain_type || !ad_vol->display_grid || !ad_vol->refl_ALA) {
        free_vol_scan(ad_vol);
        return NULL;
    }

    // Copy data
    memcpy(ad_vol->grid_refl, original_vol->grid_refl, total_elements * sizeof(double));
    memcpy(ad_vol->grid_height, original_vol->grid_height, total_elements * sizeof(double));
    memcpy(ad_vol->grid_att, original_vol->grid_att, total_elements * sizeof(double));
    memcpy(ad_vol->grid_rain_type, original_vol->grid_rain_type, total_elements * sizeof(int));

    // Copy the empirical VPRs
    memcpy(ad_vol->emp_vpr_strat, emp_vpr_strat, 120 * sizeof(double));
    memcpy(ad_vol->emp_vpr_conv, emp_vpr_conv, 120 * sizeof(double));

    return ad_vol;
}




void combine_vpr_M0(Vol_scan *vol, double vpr_strat[120], double vpr_conv[120]) {
      // replace emp_vpr_strat with vpr_strat
    for (int i = 0; i < 40; i++) {
        double ext_count = vpr_strat[i];
        
        // replace count (just add)
        vol->emp_vpr_strat[i] =ext_count;;
        
        // replace mean
	double ext_mean = vpr_strat[40 + i];
        vol->emp_vpr_strat[40 + i] = ext_mean;
       
       // replace standard deviations	
        double ext_sd = vpr_strat[80 + i];
        vol->emp_vpr_strat[80 + i] = ext_sd;
    }
    
    // replace emp_vpr_conv with vpr_conv
    for (int i = 0; i < 40; i++) {
        double ext_count = vpr_conv[i];
        
        // replace counts (just add)
        vol->emp_vpr_conv[i] = ext_count;
        
        // replace means (weighted average)
        double ext_mean = vpr_conv[40 + i];
        vol->emp_vpr_conv[40 + i] = ext_mean;
        
        //  replacestandard deviations (weighted)
        double ext_sd = vpr_conv[80 + i];
        vol->emp_vpr_conv[80 + i] = ext_sd;
    }
}



void combine_vpr_M1(Vol_scan *vol, double vpr_strat[120], double vpr_conv[120]) {
      // Combine emp_vpr_strat with vpr_strat
    for (int i = 0; i < 40; i++) {
        double vol_count = vol->emp_vpr_strat[i];
        double ext_count = vpr_strat[i];
        double total_count = vol_count + ext_count;
        
        // Calculate weights based on sample proportions
        double weight_vol = vol_count / total_count;
        double weight_ext = ext_count / total_count;
        
        // Combine counts (just add)
        vol->emp_vpr_strat[i] = total_count;
        
        // Combine means (weighted average)
        double vol_mean = vol->emp_vpr_strat[40 + i];
        double ext_mean = vpr_strat[40 + i];
        vol->emp_vpr_strat[40 + i] = (weight_vol * vol_mean) + (weight_ext * ext_mean);
        
        // Combine standard deviations (weighted)
        double vol_sd = vol->emp_vpr_strat[80 + i];
        double ext_sd = vpr_strat[80 + i];
        vol->emp_vpr_strat[80 + i] = (weight_vol * vol_sd) + (weight_ext * ext_sd);
    }
    
    // Combine emp_vpr_conv with vpr_conv
    for (int i = 0; i < 40; i++) {
        double vol_count = vol->emp_vpr_conv[i];
        double ext_count = vpr_conv[i];
        double total_count = vol_count + ext_count;
        
        // Calculate weights based on sample proportions
        double weight_vol = vol_count / total_count;
        double weight_ext = ext_count / total_count;
        
        // Combine counts (just add)
        vol->emp_vpr_conv[i] = total_count;
        
        // Combine means (weighted average)
        double vol_mean = vol->emp_vpr_conv[40 + i];
        double ext_mean = vpr_conv[40 + i];
        vol->emp_vpr_conv[40 + i] = (weight_vol * vol_mean) + (weight_ext * ext_mean);
        
        // Combine standard deviations (weighted)
        double vol_sd = vol->emp_vpr_conv[80 + i];
        double ext_sd = vpr_conv[80 + i];
        vol->emp_vpr_conv[80 + i] = (weight_vol * vol_sd) + (weight_ext * ext_sd);
    }
}


