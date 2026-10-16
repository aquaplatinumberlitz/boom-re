"""Export user-set names/comments from the open IDA database to decomp/ida_names.json.

Run inside IDA (File > Script file) or via idalib / ida MCP: exec(open('tools/ida_export_names.py').read())
Counterpart: tools/ida_apply_names.py
"""
import json, os, re
import idautils, idc, ida_bytes

SKIP = re.compile(r"^(sub_|loc_|unk_|byte_|word_|dword_|off_|qword_|stru_|asc_|a[A-Z0-9]|j_|nullsub_|unknown_libname|\?\?|__)")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "tools", "..", "decomp", "ida_names.json")
names, cmts = {}, {}
for ea, n in idautils.Names():
    if SKIP.match(n):
        continue
    if ida_bytes.is_code(ida_bytes.get_flags(ea)) or n.startswith(("vt_", "g_")):
        names["%X" % ea] = n
for ea in [int(k, 16) for k in names]:
    for rep in (0, 1):
        c = idc.get_cmt(ea, rep)
        if c:
            cmts["%X" % ea] = [rep, c]
json.dump({"names": names, "comments": cmts}, open(path, "w"), indent=0, sort_keys=True)
print("exported %d names, %d comments -> %s" % (len(names), len(cmts), path))
