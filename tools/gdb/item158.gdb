set pagination off
break *0x715E90
commands
silent
printf "ON158 a3=%x\n", *(int*)($esp+8)
continue
end
break *0x6F001E
commands
silent
printf "CLEAR117 a2=%x a3=%x\n", *(int*)($esp+4), *(int*)($esp+8)
continue
end
break *0x706E0A
commands
silent
printf "APPLY706E0A slot=%x kind=%x\n", *(int*)($esp+4), *(int*)($esp+8)
continue
end
break *0x6EAD6F
commands
silent
printf "APPLY6EAD6F\n"
continue
end
continue
printf "END\n"
quit
