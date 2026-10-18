set pagination off
break *0x6c36c7
commands
silent
printf "VF153 arg=%d state=%d\n", *(int*)($esp+4), *(int*)($ecx+4777*4)
continue
end
break *0x8ea9f9
commands
silent
printf "MASTER ret=%d\n", $eax
continue
end
break *0x6c3557
commands
silent
printf "SEND88 id=%d state=%d\n", *(int*)($esp+4), *(int*)($ecx+4777*4)
continue
end
continue
