/**
 * @file common.h
 * @brief collection of common structures and functions used
 *
 */


#ifndef COMMON_H
#define COMMON_H

#include <math.h>

/** @brief Converting an angle from radians to degrees*/
#define RAD2DEG (180.0 / M_PI)

/** @brief Converting an angle from degrees to radians*/
#define DEG2RAD (M_PI / 180.0)

/** 
 * @struct Point
 * @brief A 2D point or various vector spaces.
 *
 * Can either be in a horizontal 2D plane, or a vertical 2D plane.
 *
 */
typedef struct Point {
	double x;/**< X-coordinate in space */
	double y;/**< Y-coordinate in horizontal OR Z-coordinate in vertical */

} Point;


/**
 * @struct Bounding_box
 * @brief A box around the non-zero region of the simulation domain
 *
 * When used in azimuthal radar scans (PPI's) this box encapsulates the polar sector annulus containing a raincell.
 * When used in vertical radar scans (RHI's) this box encapsulates the strange curved rectangle containing a raincell.
 * The top,bottom, left, right are relative to the positive quadrant in Cartesian space (this only makes a difference in RHI's)
 *
 */
typedef struct Bounding_box {
        double time;
        Point topLeft;
        Point topRight;
        Point bottomLeft;
        Point bottomRight;
} Bounding_box;                         

/** 
 * @brief [DEBUG] helper function to check the physical meaning of the boxes
 */
void print_bounding_box(const Bounding_box* box);


#endif /* COMMON_H */
