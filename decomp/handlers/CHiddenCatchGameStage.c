// CHiddenCatchGameStage vf51 @ 0x47c180
int __thiscall CHiddenCatchGameStage__vf51(_DWORD *this, _DWORD *Block)
{
  _DWORD *v2; // edi
  unsigned int v4; // ecx
  unsigned int v5; // ecx
  unsigned int v6; // ecx
  unsigned int v7; // ecx
  unsigned int v8; // ecx
  unsigned int v9; // ecx
  int v10; // eax
  unsigned int v11; // ebx
  int v12; // eax
  _DWORD *v13; // eax
  int (__thiscall **v14)(int); // eax
  HWND v15; // eax
  unsigned int v16; // ecx
  unsigned int v17; // ecx
  unsigned int v18; // ecx
  unsigned int v19; // ecx
  int v20; // eax
  int v21; // edi
  int v22; // eax
  int v23; // eax
  int v25; // [esp-10h] [ebp-5Ch] BYREF
  int v26; // [esp-Ch] [ebp-58h]
  int v27; // [esp-8h] [ebp-54h]
  BOOL v28; // [esp-4h] [ebp-50h]
  int v29; // [esp+0h] [ebp-4Ch]
  int v30; // [esp+4h] [ebp-48h]
  int *v31; // [esp+10h] [ebp-3Ch]
  _DWORD *v32; // [esp+14h] [ebp-38h]
  bool v33; // [esp+1Bh] [ebp-31h]
  signed int i; // [esp+1Ch] [ebp-30h]
  _BYTE v35[40]; // [esp+20h] [ebp-2Ch] BYREF
  int v36; // [esp+48h] [ebp-4h]

  v2 = Block;
  v32 = Block;
  v4 = (unsigned __int16)RecvPkt__Decode2(this: Block);
  if ( v4 > 0x251 )
  {
    v16 = v4 - 594;
    if ( v16 != 0 )
    {
      v17 = v16 - 1;
      if ( v17 != 0 )
      {
        v18 = v17 - 2;
        if ( v18 != 0 )
        {
          v19 = v18 - 4;
          if ( v19 != 0 )
          {
            if ( v19 == 5 )
              sub_456C3D(a1: 1);
            goto LABEL_41;
          }
          if ( *(this + 5680) == 0 || (unsigned __int8)sub_43C4F8() == 0 )
          {
            sub_6FFFDB(a1: this);
            v20 = sub_6E5C77(a1: 0);
            v21 = v20;
            if ( v20 != 0 && sub_58D4DA(a1: v20) != 0 )
            {
              i = sub_594CC6(a1: v21);
              sub_6FFFDB(a1: this);
              if ( sub_6E5D7D(a1: 0) == 0 || sub_5B760E(a1: i) == 0 )
              {
                sub_6FFFDB(a1: this);
                if ( sub_6E5D7D(a1: 0) != 0 )
                {
                  v22 = sub_6FFFDB(a1: this);
                  v23 = sub_6E204D(a1: v22);
                  if ( sub_6E1AB3(a1: v23) != 0 )
                    (*(void (__thiscall **)(int))(*(_DWORD *)(v21 + 1524) + 116))(a1: v21 + 1524);
                }
                v2 = v32;
                goto LABEL_41;
              }
              sub_5B8A8B(a1: i);
            }
          }
          return sub_9DB5CB();
        }
        v31 = (int *)RecvPkt__Decode4(this: Block);
        v32 = (_DWORD *)RecvPkt__Decode4(this: Block);
        sub_4576D7(a1: v31);
        sub_4576E3(a1: v32);
      }
      else
      {
        sub_479C69(a1: Block);
      }
    }
    else
    {
      sub_479D1D(a1: v29, a2: v30);
    }
LABEL_41:
    RecvPkt__Rewind(this: v2);
    CGameStage__OnPacket(this, a2: v2);
    return sub_9DB5CB();
  }
  if ( v4 == 593 )
  {
    std::string::string(Str: aHiddencatchBan);
    v36 = 0;
    v28 = true;
    v27 = 0x10000000;
    v26 = 0x10000000;
    v12 = sub_A2A5E0(a1: 0, a2: 76, a3: 161);
    v31 = &v25;
    v13 = (_DWORD *)sub_98DB56(a1: v35, a2: v12);
    if ( v13[5] >= 0x10u )
      v13 = (_DWORD *)*v13;
    sub_5FABCC(a1: v13, a2: 0, a3: dword_EEEBD8, a4: v25, a5: v26, a6: v27, a7: v28);
    v36 = -1;
    std::string::_Tidy(a1: v35, a2: 1, Size: 0);
    sub_708FFE(a1: 0, a2: 0);
    v14 = *(int (__thiscall ***)(int))(dword_E60A08 + 8);
    v28 = true;
    v15 = (HWND)(*v14)(a1: dword_E60A08 + 8);
    FlashWindow(hWnd: v15, bInvert: v28);
    goto LABEL_41;
  }
  v5 = v4 - 77;
  if ( v5 != 0 )
  {
    v6 = v5 - 96;
    if ( v6 != 0 )
    {
      v7 = v6 - 411;
      if ( v7 != 0 )
      {
        v8 = v7 - 3;
        if ( v8 != 0 )
        {
          v9 = v8 - 2;
          if ( v9 != 0 )
          {
            if ( v9 == 1 )
            {
              v33 = RecvPkt__DecodeBool(this: Block);
              sub_4576C3(a1: this + 5572);
              if ( v33 )
              {
                for ( i = 0; i < sub_414543(a1: this + 4781); ++i )
                {
                  sub_6FFFDB(a1: this);
                  v10 = sub_6E5C77(a1: i);
                  if ( v10 != 0 )
                    (*(void (__thiscall **)(int, int, int, int))(*(_DWORD *)(v10 + 1528) + 24))(
                      a1: v10 + 1528,
                      a2: 266,
                      a3: 1,
                      a4: 1);
                }
              }
            }
          }
          else
          {
            v11 = RecvPkt__Decode4(this: Block);
            v32 = (_DWORD *)RecvPkt__Decode4(this: Block);
            v31 = (int *)RecvPkt__Decode4(this: Block);
            i = RecvPkt__Decode4(this: Block);
            if ( sub_4793B3(a1: this) != 0 )
            {
              sub_4793B3(a1: this);
              if ( (_DWORD *)sub_456FB0(a1: v11) == v32 )
              {
                sub_6734D5(a1: (void *)0x1DB, a2: 0, a3: 0);
                sub_43CBCF(a1: v31, a2: i);
              }
            }
          }
        }
        else
        {
          sub_47B083(Block);
        }
        goto LABEL_41;
      }
      sub_47B411(a1: Block);
    }
    else
    {
      (*(void (__thiscall **)(_DWORD *, _DWORD *))(*this + 596))(a1: this, a2: Block);
    }
  }
  return sub_9DB5CB();
}