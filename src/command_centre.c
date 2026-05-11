#include "control_centre.h"
#include "common.h"
#include "radars.h"
#include "material_coords_raincell.h"
#include "spatial_coords_raincell.h"
#include "vertical_profiles.h"
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <math.h>

static int global_command_id = 0;

// Worker ID support
char g_worker_id[16] = "";  // empty string = original behavior

void set_worker_id(const char *id) {
    if (id && id[0]) {
        snprintf(g_worker_id, sizeof(g_worker_id), "_%s", id);
    } else {
        g_worker_id[0] = '\0';
    }
}

// ---------------------- Logging ----------------------
FILE *log_file = NULL;

FILE *open_log_file_with_timestamp() {
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    if (!t) return NULL;

    char filename[256];
    char logs_dir[256];
    snprintf(logs_dir, sizeof(logs_dir), "logs%s", g_worker_id);
    snprintf(filename, sizeof(filename), "%s/control_centre_%Y-%m-%d_%H-%M-%S.log", logs_dir, t);

    // This is a simplified version - use strftime properly
    strftime(filename, sizeof(filename), logs_dir, t);
    // Actually, simpler approach:
    char actual_filename[512];
    strftime(actual_filename, sizeof(actual_filename), "control_centre_%Y-%m-%d_%H-%M-%S.log", t);
    snprintf(filename, sizeof(filename), "%s/%s", logs_dir, actual_filename);

    FILE *log_file = fopen(filename, "a");
    if (!log_file) {
        fprintf(stderr, "Failed to open log file %s\n", filename);
    }
    return log_file;
}

static void log_message(const char *format, ...) {
    if (!log_file) return;

//    va_list args;
//    va_start(args, format);
//    vfprintf(log_file, format, args);
//    fflush(log_file);
//    va_end(args);
return;  // Just return immediately

}

// ---------------------- Command Generation ----------------------

//#define FIVE_MINUTES 5.0  // minutes
// #define FIVE_MINUTES 300.0  // seconds
//#define FIVE_MINUTES 2.5 //minutes
#define FIVE_MINUTES 1.0 //minutes			 //
			 //
// RHI THINGS
//#define SCANS_PER_FILE 5 

// VOLUME to CAPPI things
//#define SCANS_PER_FILE 15
//#define SCANS_PER_FILE 10
#define SCANS_PER_FILE 3

void generate_commands_file(int file_index, double start_time) {
    char filename[256];
    snprintf(filename, sizeof(filename), "inputs%s/commands_%04d.txt", g_worker_id, file_index);

    FILE *file = fopen(filename, "w");
    if (!file) {
        fprintf(stderr, "Failed to create command file %s\n", filename);
        return;
    }

    double interval = FIVE_MINUTES / (SCANS_PER_FILE);  // frequency of scans
    int counter_A = 0;
    for (int i = 0; i < SCANS_PER_FILE; i++) {
        Command cmd;
        cmd.time = start_time + i * interval;
        cmd.radar_id = 2; // make sure the radar id is correct.

        // RHI THINGS    
        // snprintf(cmd.scan_mode, sizeof(cmd.scan_mode), "RHI");
        // cmd.other_angle = 0;

        // VOL->PPI THINGS
        snprintf(cmd.scan_mode, sizeof(cmd.scan_mode), "PPI");
        //double VCP_elevation_angles[SCANS_PER_FILE] = {12.0, 8.0, 4.5, 2.0, 0.8, 0.3, 25, 20, 15, 10, 6, 2.8, 1.2, 0.3, 0.3}; 
       //double VCP_elevation_angles[SCANS_PER_FILE] = {12.0, 4.5, 2.0, 0.8, 0.3, 10, 6, 2.8, 1.2, 0.3}; 
        double VCP_elevation_angles[SCANS_PER_FILE] = {1.2, 0.8, 0.3}; 
        
       	cmd.other_angle = VCP_elevation_angles[counter_A];
        cmd.raincell_id = 1;
        counter_A++;

        fprintf(file, "%.2f %d %s %d %.5f\n",
                cmd.time,
                cmd.radar_id,
                cmd.scan_mode,
                cmd.raincell_id,
                cmd.other_angle);
    }

    fclose(file);
}

// ---------------------- Command Validation ----------------------
bool validate_command(const Command *cmd) {
    if (cmd->radar_id != 1 && cmd->radar_id != 2) {
        log_message("Validation Error: Radar ID %d does not exist. Command ID %d.\n",
                    cmd->radar_id, cmd->command_id);
        return false;
    }
    if (strcmp(cmd->scan_mode, "PPI") != 0 && strcmp(cmd->scan_mode, "RHI") != 0) {
        log_message("Validation Error: Invalid scan mode '%s'. Command ID %d.\n",
                    cmd->scan_mode, cmd->command_id);
        return false;
    }
    if (cmd->raincell_id != 1) {
        log_message("Validation Error: Raincell ID %d does not exist. Command ID %d.\n",
                    cmd->raincell_id, cmd->command_id);
        return false;
    }
    return true;
}

// ---------------------- Command Execution ----------------------
void printCommand(const Command* cmd) {
    if (!cmd) return;
    printf("Command ID: %d\n", cmd->command_id);
    printf("Scheduled Time: %.2f\n", cmd->time);
    printf("Radar ID: %d\n", cmd->radar_id);
    printf("Scan Mode: %.3s\n", cmd->scan_mode);
    printf("Raincell ID: %d\n", cmd->raincell_id);
    printf("Other Angle: %.2f\n", cmd->other_angle);
    printf("============ \n\n");
}

void execute_command(const Command *cmd, Polar_box *box, const char *filename, const VPR *vpr_strat, const VPR_params *params, VPR *vpr_conv) {
    if (!cmd || !box) {
        log_message("Fatal: NULL pointer in execute_command\n");
        return;
    }

    log_message("Executing command ID %d...\n", cmd->command_id);

    const Radar* radar = find_radar_by_id_ONLY(cmd->radar_id);
    if (!radar) { log_message("Radar %d not found\n", cmd->radar_id); return; }

    const Raincell* rc = find_raincell_by_id_ONLY(cmd->raincell_id);
    if (!rc) { log_message("Raincell %d not found\n", cmd->raincell_id); return; }

    const Spatial_raincell* s_rc = find_spatial_raincell_by_id_ONLY(cmd->raincell_id);
    if (!s_rc) { log_message("Spatial Raincell %d not found\n", cmd->raincell_id); return; }

    double time_in_min = cmd->time;
    double time_in_sec = cmd->time * 60.0;
    
    // Fill and compute polar box
    if (fill_polar_box(box, time_in_sec, s_rc, radar, rc, params) != 0) {
        log_message("Failed to fill polar box for command ID %d\n", cmd->command_id);
        return;
    }

    if (strcmp(get_scanning_mode(radar), "PPI") == 0) {
        update_other_angle(box, cmd->other_angle);
    }

    Point* pos_raincell = get_position_raincell(time_in_sec, s_rc);
    log_message("Radar=(%.1f, %.1f), Raincell=(%.1f, %.1f), time=%.1f, angle=%.3f rad\n",
                radar->x, radar->y,
                pos_raincell->x, pos_raincell->y,
                time_in_sec,
                box->other_angle);
    free(pos_raincell);

    update_VPR(vpr_strat, params, time_in_sec, vpr_conv);

    fill_polar_box_grid(box, radar, s_rc, rc, time_in_sec, vpr_strat, vpr_conv);
    save_polar_box_grid_to_file(box, radar, cmd->local_scan_id, time_in_min, filename);
}

bool read_command_file_once(const char *filename, const VPR *vpr_strat, const VPR_params *params, VPR *vpr_conv) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        log_message("Error opening file '%s': %s\n", filename, strerror(errno));
        return false;
    }

    // Allocate one Polar_box and reuse it
    Polar_box* box = init_polar_box();
    if (!box) {
        fclose(file);
        log_message("Failed to initialize polar box\n");
        return false;
    }

    Command cmd;
    while (fscanf(file, "%lf %d %3s %d %lf",
                  &cmd.time,
                  &cmd.radar_id,
                  cmd.scan_mode,
                  &cmd.raincell_id,
                  &cmd.other_angle) == 5) {

        cmd.local_scan_id = global_command_id % SCANS_PER_FILE;
        cmd.command_id = (int)floor(global_command_id / SCANS_PER_FILE);
        global_command_id++;

        log_message("Processing command ID %d: scan = %d, time=%.2f, radar_id=%d, scan_mode=%s, raincell_id=%d, angle=%.2f\n",
                    cmd.command_id, cmd.local_scan_id, cmd.time, cmd.radar_id, cmd.scan_mode, cmd.raincell_id, cmd.other_angle);

        if (!validate_command(&cmd)) {
            log_message("Command ID %d failed validation. Skipping.\n", cmd.command_id);
            continue;
        }

        // Safe output file name with worker ID support
        char filenameA[256];
        snprintf(filenameA, sizeof(filenameA), "outputs%s/radar_scan_%.4d.txt", g_worker_id, cmd.command_id);

        // Execute the command safely
        execute_command(&cmd, box, filenameA, vpr_strat, params, vpr_conv);
    }

    // Free polar box once after all commands are done
    free_polar_box(box);
    fclose(file);

    log_message("Finished processing file: %s\n", filename);
    return true;
}

// ---------------------- Monitor Inputs ----------------------
void monitor_and_process_inputs(const VPR *vpr_strat, const VPR_params *params, VPR *vpr_conv) {
    int file_index = 0;

    // Create worker-specific directories
    char inputs_dir[256];
    char archive_dir[256];
    char logs_dir[256];
    
    snprintf(inputs_dir, sizeof(inputs_dir), "inputs%s", g_worker_id);
    snprintf(archive_dir, sizeof(archive_dir), "archive%s", g_worker_id);
    snprintf(logs_dir, sizeof(logs_dir), "logs%s", g_worker_id);

    if (mkdir(inputs_dir, 0755) == -1 && errno != EEXIST) {
        fprintf(stderr, "Failed to create %s directory: %s\n", inputs_dir, strerror(errno));
    }
    if (mkdir(archive_dir, 0755) == -1 && errno != EEXIST) {
        fprintf(stderr, "Failed to create %s directory: %s\n", archive_dir, strerror(errno));
    }
    if (mkdir(logs_dir, 0755) == -1 && errno != EEXIST) {
        fprintf(stderr, "Failed to create %s directory: %s\n", logs_dir, strerror(errno));
    }

    log_file = open_log_file_with_timestamp();
    if (!log_file) {
        fprintf(stderr, "Failed to open log file\n");
        return;
    }

    log_message("Monitoring started...\n");

    while (1) {
        char filename[256];
        snprintf(filename, sizeof(filename), "inputs%s/commands_%04d.txt", g_worker_id, file_index);

        char archive_filename[256];
        snprintf(archive_filename, sizeof(archive_filename), "archive%s/commands_%04d.txt", g_worker_id, file_index);

        if (access(filename, F_OK) == 0) {
            log_message("Detected file: %s. Beginning processing...\n", filename);

            if (read_command_file_once(filename, vpr_strat, params, vpr_conv)) {
                log_message("Successfully processed file: %s\n", filename);
            } else {
                log_message("Failed to process file: %s\n", filename);
            }

            if (rename(filename, archive_filename) != 0) {
                log_message("Failed to archive file %s: %s\n", filename, strerror(errno));
            } else {
                log_message("Archived file %s to %s\n", filename, archive_filename);
            }

            file_index++;
        } else {
            log_message("No file found for: %s. Stopping monitoring.\n", filename);
            break;
        }
    }

    log_message("Monitoring ended.\n");
    fclose(log_file);
    log_file = NULL;
}
