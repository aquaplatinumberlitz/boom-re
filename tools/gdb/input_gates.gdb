set pagination off
break *0x7120F6
commands
silent
printf "VF15 msg=%x key=%x st91=%x this=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($ecx+364), $ecx
continue
end
break *0x70DA84
commands
silent
printf "DA84 key=%x lp=%x down=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12)
continue
end
break *0x70DB86
commands
silent
printf "KEYMAP ret=%x\n", $eax
continue
end
break *0x708CC8
commands
silent
printf "CC8 key=%x act=%x slot=%x down=%x en=%02x/%02x/%02x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12), *(int*)($esp+16), *(unsigned char*)($ecx+0x570A), *(unsigned char*)($ecx+0x570B), *(unsigned char*)($ecx+0x570C)
continue
end
break *0x7037E7
commands
silent
printf "SETEN slot=%x val=%x\n", *(int*)($esp+4), *(int*)($esp+8)
continue
end
continue
