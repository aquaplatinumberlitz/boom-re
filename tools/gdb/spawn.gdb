set pagination off
break *0x6EC1DA
commands
silent
printf "PLACE_ALL ret=%x blk=%d,%d,%d,%d\n", *(int*)$esp, *(int*)(*(int*)($esp+16)), *(int*)(*(int*)($esp+16)+4), *(int*)(*(int*)($esp+16)+8), *(int*)(*(int*)($esp+16)+12)
continue
end
break *0x6EB788
commands
silent
printf "PLACE slot=%d x=%d y=%d\n", *(int*)($esp+8), *(int*)($esp+20), *(int*)($esp+24)
continue
end
continue
