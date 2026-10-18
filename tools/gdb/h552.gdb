set pagination off
break *0x71580C
commands
silent
printf "H552 enter this=%x pkt=%x\n", $ecx, *(int*)($esp+4)
continue
end
break *0x7158E4
commands
silent
printf "H552 exit\n"
continue
end
continue
printf "CRASH\n"
bt 6
quit
