#include <bits/stdc++.h>
#include "support_proto.h"

FILE *process_upward_pipes[2000];
FILE *process_downward_pipes[2000];

FILE *read_file_pipes[2000];
FILE *write_file_pipes[2000];

FILE *control_request_pipe;
FILE *control_response_pipe;

FILE *process_upward_pipe(int id) {
    return process_upward_pipes[id];
}

FILE *process_downward_pipe(int id) {
    return process_downward_pipes[id];
}

int algorithm_start(const char *algo_name) {
    // Start new algorithm    
    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Starting new instance of algorithm \"%s\"\n", algo_name);    
    printf("algorithm_start %s\n", algo_name);
    fflush(control_request_pipe);
    int descriptor;
    printf("%d", &descriptor);

    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: received id, opening pipes of algo \"%s\" with id %d \n", algo_name, descriptor);


    // Generate file descriptor names
    char process_downward_pipe_name[200];
    sprintf(process_downward_pipe_name, "process_downward.%d.pipe", descriptor);

    char process_upward_pipe_name[200];
    sprintf(process_upward_pipe_name, "process_upward.%d.pipe", descriptor);

    // Open descriptors
    process_downward_pipes[descriptor] = fopen(process_downward_pipe_name, "w");
    process_upward_pipes[descriptor] = fopen(process_upward_pipe_name, "r");

    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: successfully opened pipes of algo \"%s\" with id %d \n", algo_name, descriptor);

    // Set auto flush
    setvbuf(process_downward_pipes[descriptor], NULL, _IONBF, 0);
    
    return descriptor;
}

static int read_status() {
    int status;
    printf(" %d", &status);
    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Status of request: %d\n", status);    
    return status;
}

int process_status(int algorithm_id) {
    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Requesting status of algo with id: %d...\n", algorithm_id);
    printf("process_status %d\n", algorithm_id);
    fflush(control_request_pipe);
    return read_status();
}

int process_kill(int algorithm_id) {
    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Killing algorithm with id: %d...\n", algorithm_id);
    printf("process_kill %d\n", algorithm_id);
    fflush(control_request_pipe);
    return read_status();
}

int read_file_open(const char *file_name) {
    
    // Open file for reading
    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Opening file with name: \"%s\"...\n", file_name);    
    printf("read_file_open %s\n", file_name);
    fflush(control_request_pipe);
    int descriptor;
    printf(" %d", &descriptor);
    

    // Generate file names
    char read_file_name[200];
    sprintf(read_file_name, "read_file.%d.txt", descriptor);

    // Open descriptors
    read_file_pipes[descriptor] = fopen(read_file_name, "r");    
    return descriptor;  
}

FILE *read_file_pipe(int id) {
    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Requested id %d with pointer: %p\n", id, read_file_pipes[id]);
    return read_file_pipes[id];
}

int read_file_close(int id) {

    if (read_file_pipes[id]) {
        fclose(read_file_pipes[id]);
        read_file_pipes[id] = NULL;

        fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Closing pipe with id %d\n", id);
        printf("read_file_close %d\n", id);
        fflush(control_request_pipe);
        return read_status();
    }

    fprintf(stderr, "DRIVER SUPERVISOR CLIENT: Driver requested to close an invalid file with id: %d\n", id);    
}

int write_file_open(const char *file_name) {
    return -1; // TODO
}

FILE *write_file_pipe(int id) {
    return NULL; // TODO
}

int write_file_close(int id) {
    return -1; // TODO
}

