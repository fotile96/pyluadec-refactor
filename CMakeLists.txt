cmake_minimum_required(VERSION 3.24)
project(pyluadec_native LANGUAGES C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ---- apply serialization-width patch into build dir (vendor stays pristine)
set(LUA_PRISTINE ${CMAKE_SOURCE_DIR}/vendor/lua-5.1)
set(LUA_PATCHED ${CMAKE_BINARY_DIR}/lua-5.1-patched)
set(LUA_PATCHED_SRC ${LUA_PATCHED}/src)
file(REMOVE_RECURSE ${LUA_PATCHED})
file(MAKE_DIRECTORY ${LUA_PATCHED})
file(COPY ${LUA_PRISTINE}/src DESTINATION ${LUA_PATCHED})
execute_process(
  COMMAND patch -p1 -d ${LUA_PATCHED} -i ${CMAKE_SOURCE_DIR}/native/patches/0001-serial-sizet.patch
  RESULT_VARIABLE PATCH_RV OUTPUT_VARIABLE PATCH_OUT ERROR_VARIABLE PATCH_ERR)
if(NOT PATCH_RV EQUAL 0)
  message(FATAL_ERROR "lua patch failed: ${PATCH_OUT} ${PATCH_ERR}")
endif()

set(LUA_CORE_FILES
  lapi.c lcode.c ldebug.c ldo.c ldump.c lfunc.c lgc.c llex.c lmem.c
  lobject.c lopcodes.c lparser.c lstate.c lstring.c ltable.c ltm.c
  lundump.c lvm.c lzio.c
  lauxlib.c lbaselib.c ldblib.c liolib.c lmathlib.c loslib.c ltablib.c
  lstrlib.c loadlib.c linit.c)

function(add_lua_variant SUFFIX SERIAL_TYPE)
  set(srcs "")
  foreach(f ${LUA_CORE_FILES})
    list(APPEND srcs ${LUA_PATCHED_SRC}/${f})
  endforeach()
  add_library(lua_${SUFFIX} STATIC ${srcs})
  target_include_directories(lua_${SUFFIX} PUBLIC ${LUA_PATCHED_SRC})
  target_compile_definitions(lua_${SUFFIX}
    PUBLIC LUAC_SERIAL_SIZET=${SERIAL_TYPE}
    PRIVATE LUA_USE_POSIX LUA_COMPAT_ALL)

  add_executable(lua_${SUFFIX}_bin ${LUA_PATCHED_SRC}/lua.c)
  set_target_properties(lua_${SUFFIX}_bin PROPERTIES OUTPUT_NAME lua_${SUFFIX}
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
  target_link_libraries(lua_${SUFFIX}_bin PRIVATE lua_${SUFFIX} $<$<PLATFORM_ID:Linux>:m>)

  add_executable(luac_${SUFFIX}_bin ${LUA_PATCHED_SRC}/luac.c ${LUA_PATCHED_SRC}/print.c)
  set_target_properties(luac_${SUFFIX}_bin PROPERTIES OUTPUT_NAME luac_${SUFFIX}
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
  target_link_libraries(luac_${SUFFIX}_bin PRIVATE lua_${SUFFIX} $<$<PLATFORM_ID:Linux>:m>)
endfunction()

add_lua_variant(sz4 uint32_t)
add_lua_variant(sz8 uint64_t)

add_subdirectory(native)
