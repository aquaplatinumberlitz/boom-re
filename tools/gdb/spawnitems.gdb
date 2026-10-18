set pagination off
break *0x5B6578
commands
silent
printf "SPAWN a1=%x a2=%x a3=%x a4=%x a5=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12), *(int*)($esp+16), *(int*)($esp+20)
continue
end
break *0x89AEA3
commands
silent
printf "REG kind=%x index=%x\n", *(int*)($esp+4), *(int*)($esp+8)
continue
end
continue
printf "END\n"
quit
