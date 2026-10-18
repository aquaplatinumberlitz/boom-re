set pagination off
break *0x7064AC
commands
silent
printf "ON152\n"
continue
end
break *0x6E9AF9
commands
silent
printf "PLACE6E9AF9 slot=%x a3=%x a10=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+40)
continue
end
break *0x578BA3
commands
silent
printf "OWNER_VF20 this=%x desc=%x\n", $ecx, *(int*)($esp+4)
continue
end
break *0x591209
commands
silent
printf "SETID bomb=%x id=%x ret=%x\n", $ecx, *(int*)($esp+4), *(int*)$esp
continue
end
break *0x7324C0
commands
silent
printf "PLACE7324C0 bomb=%x a2=%x\n", $ecx, *(int*)($esp+4)
continue
end
continue
printf "END\n"
quit
