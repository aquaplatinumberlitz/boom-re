set pagination off
set $n4 = 0
set $n5 = 0
set $n8 = 0
break *0x6F18F4
commands
silent
set $n4 = $n4 + 1
if $n4 < 6
printf "VF4 #%d this=%x ret=%x arg=%x\n", $n4, $ecx, *(int*)$esp, *(int*)($esp+4)
end
continue
end
break *0x6F19B5
commands
silent
set $n5 = $n5 + 1
if $n5 < 6
printf "VF5 #%d this=%x ret=%x arg=%x cnt0=%x\n", $n5, $ecx, *(int*)$esp, *(int*)($esp+4), **(int**)($ecx+0x44)
end
continue
end
break *0x6F06ED
commands
silent
set $n8 = $n8 + 1
printf "VF8 #%d this=%x ret=%x slot=%x\n", $n8, $ecx, *(int*)$esp, *(int*)($esp+4)
continue
end
break *0x6EFEDC
commands
silent
printf "SETTER exit\n"
continue
end
continue
printf "CRASH n4=%d n5=%d n8=%d\n", $n4, $n5, $n8
quit
