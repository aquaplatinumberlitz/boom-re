set pagination off
break *0x6e0dc9
commands
silent
printf "L_FILTER eax=%x v=%x\n", $eax, 0
continue
end
break *0x6e0ddb
commands
silent
printf "L_GROUP eax=%x v=%x\n", $eax, 0
continue
end
break *0x6e0df2
commands
silent
printf "L_GRPOPEN eax=%x v=%x\n", $eax, *(int*)$edi
continue
end
break *0x6e0e01
commands
silent
printf "L_C3FD eax=%x v=%x\n", $eax, 0
continue
end
break *0x6e0e05
commands
silent
printf "L_ADD eax=%x v=%x\n", $eax, 0
continue
end
break *0x6dee56
commands
silent
printf "F_MODE eax=%x v=%x\n", $eax, 0
continue
end
break *0x6e0d2c
commands
silent
printf "LIST_BUILD eax=%x v=%x\n", $eax, 0
continue
end
continue
