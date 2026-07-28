/**
 * @file common.c
 * @brief common functions used throughout the project
 *
 */

#include "common.h"
#include <stdlib.h>
#include <math.h>
#include <stdio.h>


void print_bounding_box(const Bounding_box* box) {
    printf("Bounding Box:\n");

    printf("  Top Left     : (%.2f, %.2f)\n", box->topLeft.x, box->topLeft.y);
    printf("  Top Right    : (%.2f, %.2f)\n", box->topRight.x, box->topRight.y);
    printf("  Bottom Left  : (%.2f, %.2f)\n", box->bottomLeft.x, box->bottomLeft.y);
    printf("  Bottom Right : (%.2f, %.2f)\n", box->bottomRight.x, box->bottomRight.y);


// Drawing a ASCII square... no real use. 
    printf("\nASCII Representation:\n");

    printf("  +------------+\n");
    printf("  |            |\n");
    printf("  |      *     |\n");
    printf("  |            |\n");
    printf("  +------------+\n");

    printf("\n");
}

void pause_programme() {
    printf("\nPress Enter to continue...");
    while (getchar() != '\n');  // Wait for Enter key
}
