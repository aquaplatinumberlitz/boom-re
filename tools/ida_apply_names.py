"""Re-apply names/comments from decomp/ida_names.json to a fresh IDA database of unpacked_ca.exe.

IDA: File > Script file... (or run via idalib / ida MCP execute_python with exec(open(...).read())).
"""
import json, os
import ida_name, idc

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "decomp", "ida_names.json")
data = json.load(open(path))
ok = 0
for ea, n in data["names"].items():
    if ida_name.set_name(int(ea, 16), n, ida_name.SN_NOWARN | ida_name.SN_NOCHECK | ida_name.SN_FORCE):
        ok += 1
for ea, (rep, c) in data["comments"].items():
    idc.set_cmt(int(ea, 16), c, rep)
print("applied %d/%d names, %d comments" % (ok, len(data["names"]), len(data["comments"])))
