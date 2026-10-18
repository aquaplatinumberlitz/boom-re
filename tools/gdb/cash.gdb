set pagination off
break *0x9B691A
commands
silent
printf "SETCASH this=%x slot=%d val=%d ret=%x\n", $ecx, *(int*)($esp+4), *(int*)($esp+8), *(int*)$esp
continue
end
break *0x9B6E63
commands
silent
printf "GETCASH slot=%d ret=%x val=%d\n", *(int*)($esp+4), *(int*)$esp, *(int*)($ecx+12*(*(int*)($esp+4))+348+4)
continue
end
continue
