set pagination off
break *0x708CC8
commands
silent
printf "CC8 key=%x act=%x slot=%x down=%x s5395=%x list=%x ctx=%x\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12), *(int*)($esp+16), *(int*)($ecx+0x5450), *(int*)($ecx+0x5494), *(int*)($ecx+0x547C)
continue
end
break *0x708D2B
commands
silent
printf "BA5B ret=%x\n", $eax
continue
end
break *0x708E03
commands
silent
printf "STRAT obj=%x vt=%x fn=%x\n", $ecx, *(int*)$ecx, *(int*)(*(int*)$ecx+0x44)
continue
end
break *0x708E06
commands
silent
printf "STRAT ret=%x\n", $eax
continue
end
break *0x708E2B
commands
silent
printf "CTX32 obj=%x vt=%x fn=%x args=%x %x %x %x %x\n", $ecx, *(int*)$ecx, *(int*)(*(int*)$ecx+0x20), *(int*)($esp), *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12), *(int*)($esp+16)
continue
end
break *0x708E2E
commands
silent
printf "CTX32 ret=%x\n", $eax
continue
end
continue
