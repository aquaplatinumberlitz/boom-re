set pagination off
break *0x67A90D
commands
silent
printf "USI this=%x map=%x ret=%x\n", $ecx, *(int*)0xE61018, *(int*)$esp
bt 4
continue
end
continue
