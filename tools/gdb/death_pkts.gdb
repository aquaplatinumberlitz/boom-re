set pagination off
break *0x88851B if (*(int*)($esp+4) == 120 || *(int*)($esp+4) == 162 || *(int*)($esp+4) == 146)
commands
silent
printf "GROUP op=%d\n", *(int*)($esp+4)
bt 8
continue
end
continue
printf "END\n"
quit
