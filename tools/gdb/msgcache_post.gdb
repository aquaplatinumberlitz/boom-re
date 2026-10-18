set pagination off
break *0x6EFD24
commands
silent
printf "ENTRY this=%x slot=%x a2C=%x\n", $ecx, *(int*)($esp+8), *(int*)($esp+52)
continue
end
break *0x6EFEDC
commands
silent
printf "EXIT eax=%x ebp=%x\n", $eax, $ebp
continue
end
break *(*(int*)0xC546CC)
commands
silent
printf "VF8 this=%x cnt0=%x\n", $ecx, **(int**)($ecx+0x44)
continue
end
continue
printf "CRASH\n"
bt 8
quit
