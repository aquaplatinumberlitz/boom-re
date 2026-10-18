set pagination off
break *0x6EFD24
commands
silent
set $stage = $ecx - 0x4AC0
set $ctx = *(int*)($stage + 5407*4)
printf "STAGE %x CTX %x\n", $stage, $ctx
dump binary memory /home/admin/boom-re/logs/stagedump/stage.bin $stage ($stage+0x60000)
printf "DUMPED stage\n"
dump binary memory /home/admin/boom-re/logs/stagedump/ctx.bin $ctx ($ctx+0x200000)
printf "DUMPED ctx\n"
detach
quit
end
continue
printf "CRASH\n"
quit
