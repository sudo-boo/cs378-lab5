#include "simulation.h"

#include <fstream>
#include <iostream>

extern "C" bool log_enabled;
extern "C" bool grading_view;
extern "C" char const* logfile_prefix;
extern "C" char const* args[3];
extern "C" size_t delay_ms;

extern "C" void parse(int ac, char** av);

int main(int ac, char** av)
{
    parse(ac, av);

    std::map<std::string, Simulation::NT> m = {
        { "naive", Simulation::NT::NAIVE },
        { "blaster", Simulation::NT::BLASTER },
        { "rp", Simulation::NT::RP },
    };
    if (m.count(args[0]) == 0) {
        std::cerr << "Bad node type '" << args[0] << "', should be one of 'naive', 'blaster', or 'rp'\n";
        return 1;
    }

    std::ifstream net_spec_file(args[1]);
    if (!net_spec_file.is_open()) {
        std::cerr << "Unable to open file '" << args[1] << "' for reading\n";
        return 1;
    }
    std::ifstream msg_file(args[2]);
    if (!msg_file.is_open()) {
        std::cerr << "Unable to open file '" << args[2] << "' for reading\n";
        return 1;
    }

    Simulation s(m[args[0]], !!log_enabled, logfile_prefix, net_spec_file, delay_ms, !!grading_view);
    s.run(msg_file);
}
