set pagination off
set $n = 0
break *0x70C5DC
commands
silent
printf "PHASE set=%d old=%d\n", *(int*)($esp+4), *(int*)($ecx+0x5468)
continue
end
break *0x70E511
commands
silent
printf "PLAY189 mapid=%x phase=%d\n", *(int*)($esp+4), *(int*)($ecx+0x5468)
continue
end
break *0x70E5C4
commands
silent
printf "ON189 phase=%d\n", *(int*)($ecx+0x5468)
continue
end
break *0x70572A if ($n = $n + 1) % 400 == 1
commands
silent
set $t = *(int*)($ecx+0x5378)
printf "TICK n=%d a2=%x a3=%x clk=%x st=%x f3=%x base=%x pz=%x pa=%x acc=%x\n", $n, *(int*)($esp+4), *(int*)($esp+8), $t, *(int*)($t+8), *(int*)($t+12), *(int*)($t+16), *(int*)($t+24), *(int*)($t+40), *(int*)($t+48)
continue
end
continue
