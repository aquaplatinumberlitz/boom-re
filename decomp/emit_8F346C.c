// block 0x8f346c -> None   stop=unmapped 0x46c8586e from 0x46c8586e   insns=4618866
// PARTIAL: khối không chạy tới cont — các hiệu ứng dưới đây KHÔNG đầy đủ.

void vm_block_8F346C(void *self)
{
    // 22 lần ghi vào .data/.text ngoài section VM (thường là scratch của VM)
    // 180 địa chỉ là stack của VM (bỏ qua)
    // 12 địa chỉ ngoài stack — kiểm tra tay:
    //   0x20b000 n=10 last=0x14fd4f2b
    //   0x6bf67f2 n=1 last=0xa5
    //   0x6bf67f3 n=1 last=0x67
    //   0x6bf67f4 n=1 last=0x32a77b11
    //   0x6bf67f8 n=1 last=0x446efb83
    //   0x6bf67fc n=1 last=0x8b9fbb4a
    //   0x6bf6800 n=1 last=0x0
    //   0x6bf6801 n=1 last=0x0
    //   0x6bf6802 n=1 last=0xb0
    //   0x6bf67f0 n=1 last=0xf
    //   0x6c45bcc n=1 last=0x13
    //   0x6c45b90 n=1 last=0x2b
    // chuỗi gọi native, đúng thứ tự quan sát được (ecx = con trỏ this)
    call_888462((void *)0x19c3a8, 0xf, 0x46c8593e);   // #0
    call_A65280((void *)0x19c3a8, 0x4aba478, 0x46c8593e);   // #1
    call_A65280((void *)0x19c3a8, 0x0, 0x46c8593e);   // #2
    call_A65280((void *)0x19c3a8, 0x0, 0x46c8593e);   // #3
    call_8F2B34((void *)0x19c333, 0x46c8593e, 0xda05008);   // #4
    call_692EC4((void *)0x19c332, 0x46c8593e, 0xda05008);   // #5
    call_888609((void *)0x19c3a8, 0x46c8593e, 0xda05008);   // #6

}
