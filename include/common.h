/**
 * @file common.h
 * @brief collection of common structures and functions used
 *
 */


#ifndef COMMON_H
#define COMMON_H

#include <math.h>


extern double height;

#define RAD2DEG (180.0 / M_PI)
#define DEG2RAD (M_PI / 180.0)
typedef struct Point {
	double x;
	double y;
} Point;



typedef struct Bounding_box {
        double time;
        Point topLeft;
        Point topRight;
        Point bottomLeft;
        Point bottomRight;
} Bounding_box;                         

// Getter function declarations
double get_bounding_box_time(const Bounding_box* box);
Point get_bounding_box_top_left(const Bounding_box* box);
Point get_bounding_box_top_right(const Bounding_box* box);
Point get_bounding_box_bottom_left(const Bounding_box* box);
Point get_bounding_box_bottom_right(const Bounding_box* box);

int is_point_inside_box(const Point* p, const Bounding_box* box); 

int does_box1_include_box2(const Bounding_box* box1, const Bounding_box* box2);


void print_bounding_box(const Bounding_box* box);


#endif /* COMMON_H */
