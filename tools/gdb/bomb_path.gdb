set pagination off
break *0x70922B
commands
silent
printf "VF61 sub=%x\n", *(int*)($esp+4)
continue
end
break *0x8F8872
commands
silent
printf "MAINWND_VF45 a2=%x a3=%x ret=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)$esp
continue
end
break *0x5B0053
commands
silent
printf "LOCAL_BOMB ret=%x\n", *(int*)$esp
continue
end
break *0x8FE911
commands
silent
printf "MODECHK a1=%x a2=%x ret=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)$esp
continue
end
continue
printf "END\n"
quit
