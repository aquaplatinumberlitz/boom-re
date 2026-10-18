set pagination off
break *0x6E1AF7
commands
silent
printf "START clk=%x arg=%x ret=%x\n", $ecx, *(int*)($esp+4), *(int*)$esp
continue
end
break *0x6E1AC8
commands
silent
printf "STOP clk=%x ret=%x T2=%x\n", $ecx, *(int*)$esp, *(int*)($ecx+8)
continue
end
break *0x6E1B3D
commands
silent
printf "PAUSE clk=%x ret=%x T2=%x\n", $ecx, *(int*)$esp, *(int*)($ecx+8)
continue
end
break *0x6E1A86
commands
silent
printf "RESUME clk=%x ret=%x T2=%x\n", $ecx, *(int*)$esp, *(int*)($ecx+8)
continue
end
break *0x71BF9A
commands
silent
printf "VF159\n"
continue
end
continue
printf "END\n"
quit
