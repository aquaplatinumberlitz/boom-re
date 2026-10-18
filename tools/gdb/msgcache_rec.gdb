set pagination off
break *0x6EFD24
commands
silent
printf "ARGS %x %x %x %x %x %x %x %x %x %x %x %x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12), *(int*)($esp+16), *(int*)($esp+20), *(int*)($esp+24), *(int*)($esp+28), *(int*)($esp+32), *(int*)($esp+36), *(int*)($esp+40), *(int*)($esp+44), *(int*)($esp+48)
continue
end
break *0x6EFEDC
commands
silent
set $t = *(int*)($ebp-0x24)
set $cnt = **(int**)($t+0x44)
set $rec = *(int*)($t+0x34) + 0x44*($cnt-1)
printf "EXIT eax=%x this=%x cnt0=%x rec=%x\n", $eax, $t, $cnt, $rec
printf "REC %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x\n", *(int*)$rec, *(int*)($rec+4), *(int*)($rec+8), *(int*)($rec+12), *(int*)($rec+16), *(int*)($rec+20), *(int*)($rec+24), *(int*)($rec+28), *(int*)($rec+32), *(int*)($rec+36), *(int*)($rec+40), *(int*)($rec+44), *(int*)($rec+48), *(int*)($rec+52), *(int*)($rec+56), *(int*)($rec+60), *(int*)($rec+64)
continue
end
continue
printf "CRASH\n"
quit
