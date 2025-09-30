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
    cg->attenuation_grid = (double *)malloc(sizeof(double) * cg->num_elements);
    
    if (!cg->grid) {
        free(cg);
	printf("Allocating grid in Cart_grid_init() failed! allocating NULL!! \n");
        return NULL;
    }

    for (int i = 0; i < cg->num_elements; i++) {
        cg->grid[i] = 0.0;
    	cg->height_grid[i] = 0.0;
    	cg->attenuation_grid[i]=0.0;
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
/*
bool getPolarBoxIndex(Point p, double c_x, double c_y, const Polar_box* box, int *range_idx, int *angle_idx) {
    double dx = p.x - c_x;
    double dy = p.y - c_y;

    double r = sqrt(dx * dx + dy * dy);

    if (r < box->min_range_gate * box->range_resolution || r > box->max_range_gate * box->range_resolution)
        return false;

    double angle = normalizeAngle(atan2(dy, dx));  // radians

    if (!isAngleBetween(angle, box->min_angle * DEG2RAD, box->max_angle * DEG2RAD))
        return false;

    // Range index
    *range_idx = (int)lround((r - box->min_range_gate * box->range_resolution) / box->range_resolution);

    // Corrected: use radians for angle_diff
    double angle_diff = normalizeAngle(angle - box->min_angle * DEG2RAD);
    *angle_idx = (int)lround(angle_diff / (box->angular_resolution * DEG2RAD));

    if (*range_idx >= (int)box->num_ranges || *angle_idx >= (int)box->num_angles)
        return false;

    return true;
}
*/


/*
bool getPolarBoxIndex(Point p, double c_x, double c_y, const Polar_box* box,
                      int *range_idx, int *angle_idx) {
    double dx = p.x - c_x;
    double dy = p.y - c_y;

    double r = sqrt(dx * dx + dy * dy);

    // --- Range check ---
    if (r <= box->min_range_gate * box->range_resolution ||
        r > box->max_range_gate * box->range_resolution)
        return false;

    // --- Angle in [0, 2π) ---
    double angle = atan2(dy, dx);
    if (angle < 0) angle += 2 * M_PI;

    double min_angle = box->min_angle * DEG2RAD;
    if (min_angle < 0) min_angle += 2 * M_PI;

    // Angular span covered by this polar box
    double span = box->num_angles * box->angular_resolution * DEG2RAD;
// 
    // Difference relative to box min angle, wrapped
    double angle_diff = angle - min_angle;
    if (angle_diff < 0) angle_diff += 2 * M_PI;

    // If angle is outside the actual span of the box, reject
    if (angle_diff > span)
        return false;

double angle_diff = fmod(angle - min_angle + 2*M_PI, 2*M_PI);
if (angle_diff > span) return false;


    // --- Range index (rounded) ---
    *range_idx = (int)floor((r - box->min_range_gate * box->range_resolution) /
                             box->range_resolution);
    if (*range_idx < 0) *range_idx = 0;
    if (*range_idx >= (int)box->num_ranges) *range_idx = box->num_ranges - 1;

    // --- Angle index (rounded) ---
    *angle_idx = (int)floor(angle_diff / (box->angular_resolution * DEG2RAD));
    if (*angle_idx < 0) *angle_idx = 0;
    if (*angle_idx >= (int)box->num_angles) *angle_idx = box->num_angles - 1;

    return true;
}


*/

bool getPolarBoxIndex(Point p,
                      double c_x,
                      double c_y,
                      const Polar_box *box,
                      int *range_idx,
                      int *angle_idx)
{
    if (!box || !range_idx || !angle_idx) return false;

    const double eps = 1e-8; // small tolerance for floating point errors

    // --- Vector from radar to point ---
    double dx = p.x - c_x;
    double dy = p.y - c_y;

    // --- Slant range ---
    double r = sqrt(dx*dx + dy*dy);

    double r_min = box->min_range_gate * box->range_resolution;
    double r_max = box->max_range_gate * box->range_resolution;

    if (r < r_min - eps || r > r_max + eps)
        return false;

    // --- Angle in [0, 2π) ---
    double angle = atan2(dy, dx);
    if (angle < 0) angle += 2*M_PI;

    double min_angle = box->min_angle * box->angular_resolution * DEG2RAD;
    if (min_angle < 0) min_angle += 2*M_PI;

    double span = box->num_angles * box->angular_resolution * DEG2RAD;
/*
    // Difference relative to box min angle, wrapped
    double angle_diff = angle - min_angle;
    if (angle_diff < 0) angle_diff += 2*M_PI;

    if (angle_diff < -eps || angle_diff > span + eps)
        return false;
*/

double angle_diff = fmod(angle - min_angle + 2*M_PI, 2*M_PI);
if (angle_diff > span + eps)
    return false;

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
    	    if (what_to_print == 2) fprintf(fp,  "%.2f ", cg->attenuation_grid[index]);    
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
/*
    // Debug logging of grid calculation
    fprintf(stderr,
        "[DEBUG] init_vol_scan:\n"
        "  min_x=%.2f, max_x=%.2f, min_y=%.2f, max_y=%.2f\n"
        "  resolution=%.4f → nx=%zu, ny=%zu → total=%zu cells\n"
        "  num_PPIs=%d → total_cells=%zu\n",
        min_x, max_x, min_y, max_y,
        res, nx, ny, num_elements,
        num_PPIs, num_elements * (size_t)num_PPIs);
*/
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
            vol->grid_att[vol_idx]    = grid->attenuation_grid ? grid->attenuation_grid[local_idx] : NAN;
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
            else fprintf(f, "%.2f ", val);
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
                vol->refl_ALA[idx] = vpr_1->CB.reflectivity;
            } else if (cls == 2) {
                vol->refl_ALA[idx] = vpr_2->CB.reflectivity;
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
    free(cg->height_grid);
    free(cg->attenuation_grid);
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
                                double *total_true_mm2_unmasked)
{
    if (!vol || !vol->display_grid || !vol->refl_ALA) return -1;

    double sum_sq = 0.0, sum_abs = 0.0, sum_bias = 0.0;
    double sum_measured = 0.0, sum_true_masked = 0.0;
    double sum_measured_mm2_ = 0.0, sum_true_mm2_ = 0.0;

    double sum_true_all = 0.0;      // unmasked
    double sum_true_mm2_all = 0.0;  // unmasked
    int count = 0, count_all = 0;

    double cell_area_km2 = cart_grid_res*0.001 * cart_grid_res*0.001;

    for (int i = 0; i < (int)vol->num_elements; ++i) {
        double dBZ_disp = vol->display_grid[i];
        double dBZ_true = vol->refl_ALA[i];

        // --- Unmasked totals: include all valid refl_ALA ---
        if (!isnan(dBZ_true)) {
            double Rtrue = dBZ_to_R(dBZ_true);
            sum_true_all += Rtrue;
            sum_true_mm2_all += Rtrue * cell_area_km2;
            count_all++;
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

    return 0;
}

