set pagination off
break *0x6dee56
commands
silent
printf "F_MODE eax=%x\n", $eax
continue
end
break *0x6dee73
commands
silent
printf "F_CE42 eax=%x\n", $eax
continue
end
break *0x6deed0
commands
silent
printf "F_CF5B eax=%x\n", $eax
continue
end
break *0x6deedf
commands
silent
printf "F_ROOMTYPE eax=%x\n", $eax
continue
end
break *0x6def06
commands
silent
printf "F_D516 eax=%x\n", $eax
continue
end
break *0x6def19
commands
silent
printf "F_F2E eax=%x\n", $eax
continue
end
break *0x6def2b
commands
silent
printf "F_C81E eax=%x\n", $eax
continue
end
break *0x6def41
commands
silent
printf "F_C856 eax=%x\n", $eax
continue
end
break *0x6def58
commands
silent
printf "F_E4CD eax=%x\n", $eax
continue
end
break *0x6def6a
commands
silent
printf "F_C43E eax=%x\n", $eax
continue
end
break *0x6defa8
commands
silent
printf "F_CD82 eax=%x\n", $eax
continue
end
break *0x6E0D2C
commands
silent
printf "LIST_BUILD\n"
continue
end
continue
