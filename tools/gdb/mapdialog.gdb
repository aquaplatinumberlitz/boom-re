set pagination off
set $n = 0
break *0x6E048D
commands
silent
printf "GROUPS_BUILD flag=%x\n", *(int*)0xEA4E68
continue
end
break *0x6E0603
commands
silent
printf "GRP_FIND ret=%d\n", $eax
continue
end
break *0x6E0654
commands
silent
printf "GRP_NEW\n"
continue
end
break *0x6E0D2C
commands
silent
printf "LIST_BUILD all=%x\n", *(int*)($esp+4)
continue
end
break *0x6E0DC9 if ($n = $n + 1) < 8
commands
silent
printf "FILTER ret=%x\n", $eax
continue
end
break *0x6E0DDB
commands
silent
printf "GROUP_OF ret=%d\n", $eax
continue
end
break *0x6E0DF0
commands
silent
printf "GROUP rec=%x open=%x cnt=%x b16=%x\n", $eax, *(int*)$eax, *(int*)($eax+4), *(unsigned char*)($eax+16)
continue
end
continue
