set pagination off
break *0x591209
commands
silent
printf "SETID bomb=%x a2=%x ret=%x\n", $ecx, *(int*)($esp+4), *(int*)$esp
continue
end
break *0x6E9994
commands
silent
printf "ON151 id=%x a3=%x a4=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12)
continue
end
break *0x6E9A0A
commands
silent
printf "ON151 found-check eax=%x\n", $eax
continue
end
break *0x7324C0
commands
silent
printf "PLACE bomb=%x a2=%x ret=%x\n", $ecx, *(int*)($esp+4), *(int*)$esp
continue
end
continue
printf "END\n"
quit
