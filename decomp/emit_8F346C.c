// block 0x8f346c -> None   stop=unmapped 0x46c8586e from 0x46c8586e   insns=4618866
// PARTIAL: khối không chạy tới cont — các hiệu ứng dưới đây KHÔNG đầy đủ.

void vm_block_8F346C(void *self)
{
    // 22 lần ghi vào .data/.text ngoài section VM (thường là scratch của VM)
    // 192 địa chỉ heap/stack bị ghi (object game) — xem JSON
    // chuỗi gọi native, đúng thứ tự quan sát được (ecx = con trỏ this)
    call_888462((void *)0x19c3a8, 0xf, 0x46c8593e);   // #0
    call_A65280((void *)0x19c3a8, 0x4aba478, 0x46c8593e);   // #1
    call_A65280((void *)0x19c3a8, 0x0, 0x46c8593e);   // #2
    call_A65280((void *)0x19c3a8, 0x0, 0x46c8593e);   // #3
    call_8F2B34((void *)0x19c333, 0x46c8593e, 0xda05008);   // #4
    call_692EC4((void *)0x19c332, 0x46c8593e, 0xda05008);   // #5
    call_888609((void *)0x19c3a8, 0x46c8593e, 0xda05008);   // #6

}
