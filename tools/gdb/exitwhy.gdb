set pagination off
break *0x8F280B
commands
printf "SETEXIT a1=%d a2=%d\n", *(int*)($esp+4), *(int*)($esp+8)
bt 10
continue
end
break *(*(int*)0xC0F198)
commands
printf "EXITPROCESS code=%d\n", *(int*)($esp+4)
bt 12
continue
end
break *(*(int*)0xC0F3B0)
commands
printf "TERMINATE code=%d\n", *(int*)($esp+8)
bt 12
continue
end
continue
printf "CRASH\n"
bt 10
quit
