#include "vertical_profiles.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>



#define WINDOW_MINUTES 5

int main() {
    clock_t start, end;
    double cpu_time_used;

    start = clock();

    /* // initial testing block 1
	VPR_params *params = malloc(sizeof(VPR_params));

    init_VPR_params(params);

    fill_VPR_params(params,
//        60.0*60, 180.0*60.0, 210.0*60.0, 240.0*60.0, 270.0*60.0,   // times
        60.0*60, 120.0*60.0, 180.0*60.0, 210.0*60.0, 240.0*60.0,   // times
        10.0, 8000.0, 2000.0,        // Echo top
        50.0, 3.0, 2.0, 1.5,       // Bright band Z
        3000.0, 1000.0, 500.0,       // Bright band heights
        20.0, 3.0, 2.0,            // Width Z
        1000.0, -500.0, 250.0,             // Width H
        0.4,                       // Ratio
        35, -3.0, 2.0, 12.0,       // Cell base Z
        500.0, 150.0, 25.0          // Cell base heights
    );

const char* stages[] = {
    "growth start",
    "growth middle",
    "mature start",
    "mature mid",
    "mature end",
    "decay mid",
    "decay end"
};


    printf("t_growth_start = %.2f\n", params->t_growth_start);
    printf("Z_et_0 = %.2f\n", params->Z_et_0);

        // Create and fill the two VPR structures
    VPR *VPR_strat = create_and_fill_VPR(params);
    VPR *VPR_conv  = create_and_fill_VPR(params);
	

    printf("strat initial VPR: \n");
    print_VPR_points(VPR_strat);
    printf("\n\n");

    printf("conv initial VPR: \n");
	print_VPR_points(VPR_conv);


printf("\n\n");

	
	
	double height_t1 = 4000;
	printf("starting to test the parametrisation work as expected in the different phases.\n +++++++++++++++\n\n+++++++++++++++\n");
for(int i = 0; i<7;i++){
	double time  = (60.0+30.0*i)*60.0;
printf("conv at %.0f minutes (%s): \n", 60.0 + 30.0 * i, stages[i]);
    update_VPR(VPR_strat, params, time, VPR_conv);
	print_VPR_points(VPR_conv);
	printf("reflectivity at %.2f km height is %.2f\n\n", height_t1, get_reflectivity_at_height(VPR_conv, height_t1));
	printf("\n\n");
}

    end = clock();

    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;

    printf("Elapsed time: %f seconds\n", cpu_time_used);

    free(params);
    */ // end of block 1

/*
    
// start of block 2, 


       VPR_params *params = malloc(sizeof(VPR_params));
    init_VPR_params(params);

      fill_VPR_params(params,
        60.0*60, 120.0*60.0, 170.0*60.0, 200.0*60.0, 230.0*60.0,
        7.0, //8000.0,
	     2000.0, 3000.0,        // Echo top
        45.0, 1.0, 1.0, 2.0,         // Bright band Z
        3000.0, 100.0, 50.0,       // Bright band heights
        15.0, 2.0, 1.0,              // Width Z
        750.0, 500.0, 250.0,       // Width H
        0.65,-0.4, -0.15,-0.1,           // Ratio
        35, -3.0, 2.0, 14.0,         // Cell base Z
        500.0, 150.0, 25.0,           // Cell base heights
	0.0005			     // gradient in dB /m.... 
    );

    VPR *VPR_strat = create_and_fill_VPR(params);
    VPR *VPR_conv  = create_and_fill_VPR(params);

    double height_min = 0.0;
    double height_max = 10000.0;
    double height_step = 50.0;
    int n_heights = (int)((height_max - height_min) / height_step) + 1;

    double time_min = 0.0;
    double time_max = 270.0 * 60.0; // seconds
    double time_step = 5.0 * 60.0;  // seconds
    int n_times = (int)((time_max - time_min) / time_step) + 1;

    FILE *f = fopen("outputs/reflectivity_profile.txt", "w");
    if (!f) {
        perror("Failed to open file");
        free(params);
        return 1;
    }

    // Header
    fprintf(f, "Height");
    for (int t = 0; t < n_times; t++) {
        double time_minutes = (time_min + t * time_step) / 60.0;
        fprintf(f, "\tT%.0f", time_minutes);
    }
    fprintf(f, "\n");

    // Heights and reflectivities
    for (int h = 0; h < n_heights; h++) {
        double height = height_min + h * height_step;
        fprintf(f, "%.2f", height);

        for (int t = 0; t < n_times; t++) {
            double time_seconds = time_min + t * time_step;
            update_VPR(VPR_strat, params, time_seconds, VPR_conv);
            double refl = get_reflectivity_at_height(VPR_conv, height);
            fprintf(f, "\t%.2f", refl);
        }
        fprintf(f, "\n");
    }

    fclose(f);

 

*/

    // Start of block 3
    //
   VPR_params *params = malloc(sizeof(VPR_params));
    init_VPR_params(params);

      fill_VPR_params(params,
        60.0*60, 120.0*60.0, 170.0*60.0, 200.0*60.0, 230.0*60.0,
        7.0, //8000.0,
	     2000.0, 3000.0,        // Echo top
        45.0, 1.0, 1.0, 2.0,         // Bright band Z
        3000.0, 100.0, 50.0,       // Bright band heights
        15.0, 2.0, 1.0,              // Width Z
        750.0, 500.0, 250.0,       // Width H
        0.65,-0.4, -0.15,-0.1,           // Ratio
        35, -3.0, 2.0, 14.0,         // Cell base Z
        500.0, 150.0, 25.0,           // Cell base heights
	0.0005			     // gradient in dB /m.... 
    );


    VPR *VPR_strat = create_and_fill_VPR(params);
    VPR *VPR_conv  = create_and_fill_VPR(params);

    VPR *VPR_A_clima = create_and_fill_VPR(params);
    multiplyVPR(VPR_A_clima, 70.0);
    VPR *VPR_A_gmd =   create_and_fill_VPR(params);

    VPR *VPR_A_d = create_and_fill_VPR(params);

    VPR *VPR_dummy = malloc(sizeof(VPR));
    
    double t1,t2, t3, timeB;
    t1 = params->t_growth_start;
    t2 = params->t_decay_end;
    t3 = params->t_mature_end;
    int num_timesteps = (int)floor((t2-t1)/60);
    int counterA = 0;
    printf("number of timesteps in domain is %d\n", num_timesteps);    
    for (int i = 0; i<num_timesteps;i++){
    	    timeB = t1 + i*60;
	    update_VPR(VPR_strat, params, timeB, VPR_dummy);
	    cumaddVPR(VPR_dummy, VPR_A_gmd);
	    cumaddVPR(VPR_dummy, VPR_A_clima);

	    if (timeB>t3) {cumaddVPR(VPR_dummy, VPR_A_d); counterA++;}
    }
    divideVPR(VPR_A_gmd, num_timesteps+1);
    divideVPR(VPR_A_d, counterA);
    // Assuming the stratiform starts from time 0 to a time 10 mins after the decay ends. 
    // 		And that this is an average raincell in the domain. 

    divideVPR(VPR_A_clima, 170+70);
print_VPR_points(VPR_strat);
print_VPR_points(VPR_A_clima);
print_VPR_points(VPR_A_gmd);
print_VPR_points(VPR_A_d);
 





// Output VPR profiles for comparison in Python
double height_min = 0.0;
double height_max = 10000.0;
double height_step = 50.0;
int n_heights = (int)((height_max - height_min) / height_step) + 1;

FILE *f = fopen("outputs/vpr_comparison.txt", "w");
if (!f) {
    perror("Failed to open output file");
    return 1;
}

// Header
fprintf(f, "Height\tVPR_A_clima\tVPR_A_gmd\tVPR_A_d\n");

// Loop through heights
for (int h = 0; h < n_heights; h++) {
    double height = height_min + h * height_step;

    double refl_clima = get_reflectivity_at_height(VPR_A_clima, height);
    double refl_gmd   = get_reflectivity_at_height(VPR_A_gmd, height);
    double refl_d     = get_reflectivity_at_height(VPR_A_d, height);

    fprintf(f, "%.2f\t%.2f\t%.2f\t%.2f\n",
            height, refl_clima, refl_gmd, refl_d);
}

fclose(f);
printf("VPR comparison file written to outputs/vpr_comparison.txt\n");


// Output VPR profiles for comparison in Pytho
//
//
//

VPR *VPR_growth = create_and_fill_VPR(params);
VPR *VPR_mature = create_and_fill_VPR(params);
VPR *VPR_decay = create_and_fill_VPR(params);

update_VPR(VPR_strat, params, params->t_mature_start, VPR_growth);
update_VPR(VPR_strat, params, params->t_mature_end, VPR_mature);
update_VPR(VPR_strat, params, params->t_decay_mid, VPR_decay);

FILE *f1 = fopen("outputs/vpr_stages.txt", "w");
if (!f1) {
    perror("Failed to open output file");
    return 1;
}

// Header
fprintf(f1, "Height\tVPR_strat\tVPR_growth\tVPR_mature\tVPR_decay\n");

// Loop through heights
for (int h = 0; h < n_heights; h++) {
    double height = height_min + h * height_step;

    double refl_1 = get_reflectivity_at_height(VPR_strat, height);
    double refl_2   = get_reflectivity_at_height(VPR_growth, height);
    double refl_3    = get_reflectivity_at_height(VPR_mature, height);
    double refl_4   = get_reflectivity_at_height(VPR_decay, height);

    fprintf(f1, "%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n",
            height, refl_1, refl_2, refl_3, refl_4);
}

fclose(f1);








free(VPR_dummy);


free(VPR_A_clima);
    free(VPR_A_gmd);
    free(VPR_A_d);


/*
// Beginning of block 4
   VPR_params *params = malloc(sizeof(VPR_params));
    init_VPR_params(params);

    fill_VPR_params(params,
        60.0*60, 120.0*60.0, 170.0*60.0, 200.0*60.0, 230.0*60.0,
        10.0, 8000.0, 2000.0,        // Echo top
        50.0, 3.0, 2.0, 2.0,         // Bright band Z
        3000.0, 100.0, 50.0,       // Bright band heights
        25.0, 4.0, 3.0,              // Width Z
        1000.0, 4500.0, 750.0,       // Width H
        0.4,-0.2, -0.15, -0.05,           // Ratio
        35, -3.0, 2.0, 15.0,         // Cell base Z
        500.0, 150.0, 25.0           // Cell base heights
    );

    VPR *VPR_strat = create_and_fill_VPR(params);
    VPR *VPR_conv  = create_and_fill_VPR(params);

    double t1,t2, timeB;
    t1 = 0.00;
    t2 = 270.00;
    int num_timesteps = (int)floor((t2-t1)/60);
    int counterA = 0;
    printf("number of timesteps in domain is %d\n", num_timesteps);    
 



FILE *f_avg = fopen("outputs/reflectivity_profile_5min_avg.txt", "w");
if (!f_avg) {
    perror("Failed to open output file for 5-min average");
    exit(1);
}







// Header
fprintf(f_avg, "Height");
for (int i = 0; i < num_timesteps; i++) {
    double time_minutes = (t1 + i * 60) / 60.0;
    fprintf(f_avg, "\tT%.0f", time_minutes);
}
fprintf(f_avg, "\n");

// Store all computed VPRs so far
VPR **history = calloc(num_timesteps, sizeof(VPR*));

for (int i = 0; i < num_timesteps; i++) {
    double timeB = t1 + i * 60;

    // Compute and store current VPR
    history[i] = calloc(1, sizeof(VPR));
    update_VPR(VPR_strat, params, timeB, history[i]);

    // Create a sum for the last 5 minutes
    VPR sumVPR = {0}; // zero-init struct
    int count = 0;

    for (int j = i; j >= 0 && j > i - WINDOW_MINUTES; j--) {
        cumaddVPR(history[j], &sumVPR);
        count++;
    }

    // Average
    divideVPR(&sumVPR, count);

double height_min = 0.0;
double height_max = 10000.0;
double height_step = 50.0;
int n_heights = (int)((height_max - height_min) / height_step) + 1;






    // Output row for each height
    for (int h = 0; h < n_heights; h++) {
        double height = height_min + h * height_step;
        double refl = get_reflectivity_at_height(&sumVPR, height);
        fprintf(f_avg, "%.2f\t", refl);
    }
    fprintf(f_avg, "\n");
}

// Cleanup
for (int i = 0; i < num_timesteps; i++) {
    free(history[i]);
}
free(history);
fclose(f_avg);
*/


/*
 // Block 5
// --- Setup parameters ---
VPR_params *params = malloc(sizeof(VPR_params));
init_VPR_params(params);

fill_VPR_params(params,
    60.0*60, 120.0*60.0, 170.0*60.0, 200.0*60.0, 230.0*60.0,
    10.0, 8000.0, 2000.0,        // Echo top
    50.0, 3.0, 2.0, 2.0,         // Bright band Z
    3000.0, 100.0, 50.0,         // Bright band heights
    25.0, 4.0, 3.0,              // Width Z
    1000.0, 4500.0, 750.0,       // Width H
    0.4, -0.2, -0.15, -0.05,     // Ratio
    35, -3.0, 2.0, 20.0,         // Cell base Z
    500.0, 150.0, 25.0           // Cell base heights
);

VPR *VPR_temp   = create_and_fill_VPR(params);
VPR *VPR_sample = create_and_fill_VPR(params);
VPR *VPR_sum    = create_and_fill_VPR(params);

double height_min = 0.0;
double height_max = 10000.0;
double height_step = 50.0;
int n_heights = (int)((height_max - height_min) / height_step) + 1;

double time_min = 0.0;
double time_max = 270.0 * 60.0; // seconds
double time_step = 1.0 * 60.0;  // seconds
int n_times = (int)((time_max - time_min) / time_step) + 1;

FILE *f = fopen("outputs/reflectivity_profile_avg.txt", "w");
if (!f) {
    perror("Failed to open file");
    free(params);
    return 1;
}

// Header
fprintf(f, "Height");
for (int t = 0; t < n_times; t++) {
    double time_minutes = (time_min + t * time_step) / 60.0;
    fprintf(f, "\tT%.0f", time_minutes);
}
fprintf(f, "\n");

// Heights and averaged reflectivities
for (int h = 0; h < n_heights; h++) {
    double height = height_min + h * height_step;
    fprintf(f, "%.2f", height);

    for (int t = 0; t < n_times; t++) {
        double time_seconds = time_min + t * time_step;

        // Reset sum profile
        memset(VPR_sum, 0, sizeof(*VPR_sum));

        // Collect samples for last 5 minutes (exc current)
        for (int m = 0; m < 1; m++) {
	    //double sample_time = time_seconds - (m+1) * 60.0;
            double sample_time = time_seconds - (m+1) * 60.0;
            if (sample_time < time_min) {
                // If not enough history, just use current time
                sample_time = time_min;
            }

            update_VPR(VPR_sample, params, sample_time, VPR_temp);
            cumaddVPR(VPR_temp, VPR_sum);
        }

        // Average
        divideVPR(VPR_sum, 5);

        // Get reflectivity for this height from averaged profile
        double avg_refl = get_reflectivity_at_height(VPR_sum, height);
        fprintf(f, "\t%.2f", avg_refl);
    }

    fprintf(f, "\n");
}

fclose(f);
*/







    end = clock();
    cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Elapsed time: %f seconds\n", cpu_time_used);

    free(params);


    return 0;
}

