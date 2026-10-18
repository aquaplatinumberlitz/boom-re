set pagination off
set $n = 0
break *0x704E16
commands
silent
printf "SELECT idx=%x ret=%x old547C=%x list=%x..%x\n", *(int*)($esp+4), *(int*)$esp, *(int*)($ecx+0x547C), *(int*)($ecx+0x5484), *(int*)($ecx+0x5488)
continue
end
break *0x71A9EC
commands
silent
printf "RESET ret=%x 547C=%x 5378=%x\n", *(int*)$esp, *(int*)($ecx+0x547C), *(int*)($ecx+0x5378)
continue
end
break *0x6E1AF7
commands
silent
printf "START clk=%x ret=%x\n", $ecx, *(int*)$esp
continue
end
break *0x70572A if ($n = $n + 1) % 600 == 1
commands
silent
printf "TICK n=%d 547C=%x 5378=%x\n", $n, *(int*)($ecx+0x547C), *(int*)($ecx+0x5378)
continue
end
continue
printf "END\n"
quit
