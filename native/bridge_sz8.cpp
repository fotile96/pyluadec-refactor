#include "bridge_impl.hpp"
PYBIND11_MODULE(_bridge_sz8, m) { pyluadec_bridge::register_bridge(m); }
