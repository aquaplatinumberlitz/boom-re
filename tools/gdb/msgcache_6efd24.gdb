set pagination off
break *0x6EFD24
commands
silent
printf "ENTRY ecx=%x vt=%x ret=%x\n", $ecx, *(int*)$ecx, *(int*)$esp
printf "ARGS %x %x %x %x %x %x %x %x %x %x %x %x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12), *(int*)($esp+16), *(int*)($esp+20), *(int*)($esp+24), *(int*)($esp+28), *(int*)($esp+32), *(int*)($esp+36), *(int*)($esp+40), *(int*)($esp+44), *(int*)($esp+48)
printf "T41 base=%x cnt3=%x\n", *(int*)($ecx+0xA4), *(int*)($ecx+12)
continue
end
break *0x6EFD3F
commands
silent
printf "GATE sub_8EAC0E=%x\n", $eax
continue
end
break *0x6F0B2A
commands
silent
printf "FLUSH112 slot=%x\n", *(int*)($esp+4)
continue
end
continue
printf "CRASH\n"
bt 8
quit
