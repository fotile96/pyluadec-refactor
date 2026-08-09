find_package(pybind11 CONFIG REQUIRED)

function(add_bridge SUFFIX)
  pybind11_add_module(_bridge_${SUFFIX} bridge_${SUFFIX}.cpp)
  target_link_libraries(_bridge_${SUFFIX} PRIVATE lua_${SUFFIX})
  set_target_properties(_bridge_${SUFFIX} PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/pyluadec/_native)
endfunction()

add_bridge(sz4)
add_bridge(sz8)
