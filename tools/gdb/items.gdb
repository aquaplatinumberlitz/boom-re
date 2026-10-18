set pagination off
break *0x6A5A5E
commands
silent
printf "ON553\n"
continue
end
break *0x729F44
commands
silent
printf "LOADITEMS\n"
continue
end
break *0x5BF485
commands
silent
printf "TILEITEM tile=%x kind=%x index=%x tx=%d ty=%d\n", $ecx, *(int*)($esp+4), *(int*)($esp+8), *(int*)($ecx+156), *(int*)($ecx+160)
continue
end
break *0x5BF711
commands
silent
printf "BRICKBREAK tile=%x tx=%d ty=%d f172=%x f176=%x\n", $ecx, *(int*)($ecx+156), *(int*)($ecx+160), *(int*)($ecx+172), *(int*)($ecx+176)
continue
end
break *0x5B6578
commands
silent
printf "SPAWNITEM\n"
continue
end
continue
printf "END\n"
quit
