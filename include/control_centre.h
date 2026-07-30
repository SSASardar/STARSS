#ifndef CONTROL_CENTRE_H
#define CONTROL_CENTRE_H

#include <stdbool.h>
#include <stdio.h>
#include "radars.h"
#include "vertical_profiles.h"


// ---------------------- Command Structure ----------------------
typedef struct {
    double time;          // Scheduled time in seconds
    int radar_id;         // Radar ID (e.g., 1 or 2)
    char scan_mode[4];    // Scan mode ("PPI" or "RHI")
    int raincell_id;      // Raincell ID (1)
    double other_angle;   // Extra parameter (e.g., elevation angle for PPI)
    int command_id;       // Unique command ID assigned internally
    int local_scan_id;	  // for id within each radar_scan_*.txt file.
} Command;

// ---------------------- Function Prototypes ----------------------
// Worker ID support
extern char g_worker_id[16];
void set_worker_id(const char *id);


// Logging
FILE *open_log_file_with_timestamp(void);
//void log_message(const char *format, ...);



// Command handling
bool validate_command(const Command *cmd);
void execute_command(const Command *cmd, Polar_box *box, const char *filename, const VPR *vpr_strat, const VPR_params *params, VPR *vpr_conv);
void printCommand(const Command *cmd);

// File handling
bool read_command_file_once(const char *filename, const VPR *vpr_strat, const VPR_params *params, VPR *vpr_conv);
bool read_command_file_once_multi_radar(const char *filename, const VPR *vpr_strat, const VPR_params *params, VPR *vpr_conv);




// Command generation
void generate_commands_file(int file_index, double start_time);
void generate_commands_file_vol_rhi_A(int file_index, double start_time);
void generate_commands_file_model_description(int file_index, double start_time); 


// Monitoring
void monitor_and_process_inputs(const VPR *vpr_strat,const VPR_params *params, VPR *vpr_conv);
void monitor_and_process_inputs_multi_radar(const VPR *vpr_strat,const VPR_params *params, VPR *vpr_conv);


#endif // CONTROL_CENTRE_H

