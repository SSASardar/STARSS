#include <stdio.h>
#include <time.h>

#define MAX_TASKS 10
#define MAX_CATEGORIES 7

typedef struct {
    const char* task;
    int completion; // percentage
} Task;

typedef struct {
    const char* category;
    Task tasks[MAX_TASKS];
    int task_count;
} Category;

void print_progress() {
    Category categories[MAX_CATEGORIES] = {
        {
            "Model of rain",
            {
                {"Holistic overview",60},
		{"Material & spatial descriptions", 80},
		{"Development convective core",80},
		{"Dynamic equil. VPR", 80},
		{"What is the ground truth?",70}
            },
            5
        },
        {
            "Model of radar",
            {
                {"Radar geometry (PPI)", 75},
		{"Radar geometry (RHI)", 60},
		{"Noise model", 80},
		{"Attenuation model",80},
		{"Clutter model",5},
		{"What to measure",40},
		{"Measurement outputs",90}
            },
            7
        },
	{
		"Radar config. & contr.",
		{
			{"Reading in commands",90},
			{"Validating commands",20},
			{"Executing commands", 80},
			{"Checking for new files",60},
			{"Saving radar outputs",90},
			{"Generating command list",75},
			{"Processing instructions",30},
		},
		6
	},
	{
		"Processing unit",
		{
			{"Reading the radar_scan file", 100},
			{"Cartesian spatial interpolation", 65},
			{"Temporal interpolation", 5},
			{"Reconstruction of VPR",5},
			{"PPI/vol scan to rainfall rate", 65},
			{"PPI-PPI to rainfall rate", 20},
			{"PPI-PPI-RHI to rainfall rate", 5},
			{"PPI-RHI to rainfall rate", 5},

		},
		8
	},
        {
            "Meteorological product",
            {
		{"Total rainfall accumulation",30},
		{"True rainfall accumulation",30},
		{"(opt) Forecast", 0}
            },
            3
        },
        {
            "Hydrological product??",
            {
		{"Entry rate of water into river",10},
		{"True rainfall accumulation",5},
		{"(opt) Forecast",0}
            },
            4
        },
        {
            "Comparative measures??",
            {
                {"Rainfall acc. map + MSE/Bias", 15},
                {"Entry rate curve + MSE/Bias", 0}
            },
            2
        }
    };

    FILE* file = fopen("progress.txt", "w");
    if (!file) {
        perror("Error opening progress.txt");
        return;
    }

    const char* header =
        "+------------------------+----------------------------------+----------------------+\n"
        "|        Category        |                Task              |        Progress      |\n"
        "+------------------------+----------------------------------+----------------------+\n";


    const char* split = 
	"+------------------------+----------------------------------+----------------------+\n";

    printf("\n\n\n%s", header);
    fprintf(file, "%s", header);

    for (int i = 0; i < MAX_CATEGORIES; i++) {
        for (int j = 0; j < categories[i].task_count; j++) {
            char progress[21];
            int stars = categories[i].tasks[j].completion / 5;
            for (int k = 0; k < 20; k++) {
                progress[k] = (k < stars) ? '#' : '.';
            }
            progress[20] = '\0';

            const char* category_name = (j == 0) ? categories[i].category : "";

            printf("| %-22s | %-32s | %-20s |\n",
                   category_name,
                   categories[i].tasks[j].task,
                   progress);

            fprintf(file, "| %-22s | %-32s | %-20s |\n",
                    category_name,
                    categories[i].tasks[j].task,
                    progress);
        }
	printf("%s", split);
	fprintf(file, "%s", split);
    }

    const char* footer =
        "+------------------------+----------------------------------+----------------------+\n";
    printf("%s", footer);
    fprintf(file, "%s", footer);
	
    const char* legend =
        "\n                                                         Legend:\n\n"
        "                                                              ####................ (≤ 30%%): Idea\n"
        "                                                              ##########.......... (≤ 50%%): Functioning implementation\n"
        "                                                              ################.... (≤ 85%%): Test-ready, but can be improved\n"
        "                                                              #################### (100%%): Complete and satisfying\n";

    printf("\n\n\n%s\n\n\n", legend);
    fprintf(file, "%s", legend);

    // -----------------------------
    // Print current date and time
    // -----------------------------
    time_t now = time(NULL);
    char time_str[64];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", localtime(&now));


	    // -----------------------------
    // Manual: Next 5 tasks to do
    // -----------------------------
    const char* next_tasks[5] = {
        " implement quality metric on heights",
	" correcting for bright band if melting layer height known",
	" reconstructed VPR based on the measurement? ",
        " combining X-band and C-band PPI's/vol scans...",
	" making a RHI with X band"
    };

    fprintf(file, "\n\n\nNext 5 tasks to prioritise (as of %s):\n", time_str);
    fprintf(file, "  1. %s\n", next_tasks[0]);
    fprintf(file, "  2. %s\n", next_tasks[1]);
    fprintf(file, "  3. %s\n", next_tasks[2]);
    fprintf(file, "  4. %s\n", next_tasks[3]);
    fprintf(file, "  5. %s\n", next_tasks[4]);

    printf("\nNext 5 tasks to prioritise (as of %s):\n", time_str);
    printf("  1. %s\n", next_tasks[0]);
    printf("  2. %s\n", next_tasks[1]);
    printf("  3. %s\n", next_tasks[2]);
    printf("  4. %s\n", next_tasks[3]);
    printf("  5. %s\n\n\n", next_tasks[4]);

    fclose(file);
}


int main(void){
	print_progress();
}
