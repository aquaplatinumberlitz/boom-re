set pagination off
set $n = 0
set $n159 = 0
set $nflush = 0
set $n5 = 0
set $n8 = 0
break *0x70572A if ($n = $n + 1) % 300 == 1
commands
silent
set $c = *(int*)($ecx+0x5378)
set $t = $c + 0x1DF05C
printf "TICK n=%d ctx=%x clk=%x started=%x f3=%x base=%x acc=%x\n", $n, $c, $t, *(int*)($t+8), *(int*)($t+12), *(int*)($t+16), *(int*)($t+48)
continue
end
break *0x71BF9A
commands
silent
set $n159 = $n159 + 1
if $n159 < 4 || $n159 % 200 == 0
printf "VF159 #%d\n", $n159
end
continue
end
break *0x6FFE4C
commands
silent
set $nflush = $nflush + 1
if $nflush < 4 || $nflush % 200 == 0
printf "FLUSHW #%d\n", $nflush
end
continue
end
break *0x6F19B5
commands
silent
set $n5 = $n5 + 1
printf "VF5 #%d cnt0=%x\n", $n5, **(int**)($ecx+0x44)
continue
end
break *0x6F06ED
commands
silent
set $n8 = $n8 + 1
printf "VF8 #%d slot=%x\n", $n8, *(int*)($esp+4)
continue
end
break *0x6EFEDC
commands
silent
printf "SETTER exit\n"
continue
end
continue
printf "END n=%d vf159=%d flushw=%d vf5=%d vf8=%d\n", $n, $n159, $nflush, $n5, $n8
quit
