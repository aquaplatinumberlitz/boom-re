set pagination off
break *0x88849F if *(int*)($esp+4) == 18
commands
silent
printf "SEND18 ret=%x ret2=%x\n", *(int*)$esp, *(int*)($ebp+4)
bt 6
continue
end
continue
