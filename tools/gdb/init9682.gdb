set pagination off
break *0x9682DE
commands
silent
printf "INIT enter this=%x idx=%x\n", $ecx, *(int*)($esp+4)
continue
end
break *0x968385
commands
silent
printf "INIT exit\n"
continue
end
continue
printf "CRASH\n"
bt 6
quit
