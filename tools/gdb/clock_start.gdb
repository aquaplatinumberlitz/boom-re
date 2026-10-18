set pagination off
break *0x6E1AF7
commands
silent
printf "START enter clk=%x arg=%x ret=%x slot16AD000=%x\n", $ecx, *(int*)($esp+4), *(int*)$esp, *(int*)0x16AD000
continue
end
break *0x6E1B3A
commands
silent
printf "START exit T2=%x T3=%x T4=%x\n", *(int*)($esi+8), *(int*)($esi+12), *(int*)($esi+16)
continue
end
break *0x6E2054
commands
silent
printf "WRAP2054 ctx=%x ret=%x\n", $ecx, *(int*)$esp
continue
end
break *0x70E357
commands
silent
printf "H189m1 sub_70E357 ret=%x\n", *(int*)$esp
continue
end
break *0x709A38
commands
silent
printf "H191 sub_709A38\n"
continue
end
set $e = 0
continue
printf "END\n"
quit
