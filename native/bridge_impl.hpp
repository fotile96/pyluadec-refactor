#pragma once
#include <pybind11/pybind11.h>
#include <memory>
#include <stdexcept>
#include <string>

extern "C" {
#include "lua.h"
#include "lauxlib.h"
#include "lobject.h"
#include "lstate.h"
#include "lundump.h"
}

namespace py = pybind11;

namespace pyluadec_bridge {

inline py::bytes tstring_to_bytes(const TString* ts) {
  return py::bytes(getstr(ts), ts->tsv.len);
}

inline py::object const_to_py(const TValue* o) {
  switch (ttype(o)) {
    case LUA_TNIL: return py::none();
    case LUA_TBOOLEAN: return py::bool_(bvalue(o) != 0);
    case LUA_TNUMBER: {
      lua_Number n = nvalue(o);
      py::dict d;
      d["type"] = "number";
      d["value"] = py::float_(static_cast<double>(n));
      d["payload"] = py::bytes(reinterpret_cast<const char*>(&n), sizeof n);
      return d;
    }
    case LUA_TSTRING: return tstring_to_bytes(rawtsvalue(o));
    default: throw std::runtime_error("unexpected constant type " + std::to_string(ttype(o)));
  }
}

inline py::dict proto_to_dict(const Proto* p) {
  py::dict d;
  d["source"] = p->source ? py::object(tstring_to_bytes(p->source)) : py::object(py::none());
  d["linedefined"] = p->linedefined;
  d["lastlinedefined"] = p->lastlinedefined;
  d["nups"] = static_cast<int>(p->nups);
  d["numparams"] = static_cast<int>(p->numparams);
  d["is_vararg"] = static_cast<int>(p->is_vararg);   // raw flags, not flattened
  d["maxstacksize"] = static_cast<int>(p->maxstacksize);

  py::list code;
  for (int i = 0; i < p->sizecode; i++)
    code.append(py::int_(static_cast<unsigned long long>(p->code[i])));
  d["code"] = code;

  py::list consts;
  for (int i = 0; i < p->sizek; i++) consts.append(const_to_py(&p->k[i]));
  d["constants"] = consts;

  py::list lineinfo;
  for (int i = 0; i < p->sizelineinfo; i++) lineinfo.append(p->lineinfo[i]);
  d["lineinfo"] = lineinfo;

  py::list locvars;
  for (int i = 0; i < p->sizelocvars; i++) {
    py::dict lv;
    lv["name"] = p->locvars[i].varname
                     ? py::object(tstring_to_bytes(p->locvars[i].varname))
                     : py::object(py::none());
    lv["startpc"] = p->locvars[i].startpc;
    lv["endpc"] = p->locvars[i].endpc;
    locvars.append(lv);
  }
  d["locvars"] = locvars;

  py::list upvalues;
  for (int i = 0; i < p->sizeupvalues; i++)
    upvalues.append(p->upvalues[i] ? py::object(tstring_to_bytes(p->upvalues[i]))
                                   : py::object(py::none()));
  d["upvalues"] = upvalues;

  py::list subs;
  for (int i = 0; i < p->sizep; i++) subs.append(proto_to_dict(p->p[i]));
  d["subprotos"] = subs;
  return d;
}

struct LuaCloser { void operator()(lua_State* L) const { if (L) lua_close(L); } };

inline py::dict load_bytecode(py::bytes blob, const std::string& chunkname) {
  std::string data = blob;   // copy; py::bytes -> std::string keeps embedded NULs
  std::unique_ptr<lua_State, LuaCloser> L(luaL_newstate());
  if (!L) throw std::runtime_error("luaL_newstate failed");
  int st = luaL_loadbuffer(L.get(), data.data(), data.size(), chunkname.c_str());
  if (st != 0) {
    const char* msg = lua_tostring(L.get(), -1);
    throw std::runtime_error(std::string("load failed (") + std::to_string(st) + "): " +
                             (msg ? msg : "?"));
  }
  const Closure* cl = static_cast<const Closure*>(lua_topointer(L.get(), -1));
  if (!cl || cl->l.isC) throw std::runtime_error("loaded chunk is not a Lua closure");
  return proto_to_dict(cl->l.p);
}

inline void register_bridge(py::module_& m) {
  m.def("load_bytecode", &load_bytecode, py::arg("blob"), py::arg("chunkname") = "=chunk");
  m.def("serial_sizet_width", [] { return static_cast<int>(sizeof(lua_SerialSizet)); });
}

}  // namespace pyluadec_bridge
