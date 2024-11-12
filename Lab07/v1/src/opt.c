#include <argp.h>
#include <stdbool.h>
#include <stdlib.h>

static char const* doc = "layer2simulator - A Layer 2 Network Simulator";
static char const* args_doc = "NODE_TYPE FILE.netspec FILE.msgs";
static struct argp_option options[] = {
    { "log", 'l', "NODE_LOG_FILE_PREFIX", OPTION_ARG_OPTIONAL, "Emit node-wise logs to file \"{NODE_LOG_FILE_PREFIX}{mac}.log\"\n(default: \"node-\")" },
    { "delay", 'd', "DELAY", 0, "Add delay in ms (50ms if unspecified)" },
    { "grading", 'g', NULL, OPTION_HIDDEN, "Enable autograding view" },
    { 0 }
};

bool log_enabled = false;
bool grading_view = false;
char const* logfile_prefix = "node-";
char const* args[3] = { 0 };
size_t delay_ms = 50;

static error_t parse_opt(int key, char* arg, struct argp_state* state)
{
    switch (key) {
    case 'l':
        log_enabled = true;
        if (arg != NULL)
            logfile_prefix = arg;
        break;
    case 'g':
        grading_view = true;
        break;
    case 'd': {
        char* a = NULL;
        delay_ms = strtol(arg, &a, 10);
        if (*a != '\0')
            argp_usage(state);
    } break;
    case ARGP_KEY_ARG:
        if (state->arg_num >= 3)
            argp_usage(state);
        args[state->arg_num] = arg;
        break;
    case ARGP_KEY_END:
        if (state->arg_num < 3)
            argp_usage(state);
        break;
    default:
        return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

void parse(int argc, char** argv)
{
    struct argp a = { options, parse_opt, args_doc, doc };
    argp_parse(&a, argc, argv, 0, 0, NULL);
}
