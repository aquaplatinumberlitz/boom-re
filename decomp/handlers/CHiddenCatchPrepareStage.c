// CHiddenCatchPrepareStage vf51 @ 0x478c84
void __thiscall CHiddenCatchPrepareStage__vf51(void *this, int *a2)
{
  int v3; // eax
  int v4; // eax
  int v5; // eax
  int v6; // eax
  int v7; // eax
  int v8; // eax
  int v9; // eax
  int v10; // eax
  int v11; // eax
  int v12; // eax
  int v13; // eax
  int v14; // eax
  int v15; // eax
  int v16; // eax
  int v17; // eax
  int v18; // eax
  int v19; // eax
  int v20; // eax
  int v21; // eax
  int v22; // eax
  int v23; // eax
  int v24; // eax
  int v25; // eax
  _BYTE v26[36]; // [esp+10h] [ebp-28h] BYREF
  int v27; // [esp+34h] [ebp-4h]

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v3 > 0xFDu )
  {
    if ( (unsigned __int16)v3 > 0x21Au )
    {
      v20 = (unsigned __int16)v3 - 553;
      if ( v20 != 0 )
      {
        v21 = v20 - 32;
        if ( v21 == 0 )
        {
          sub_456BF7(a1: a2);
          sub_9903FF(a1: 1);
          sub_475C1F();
          return;
        }
        v22 = v21 - 3;
        if ( v22 == 0 )
        {
          sub_46742C(a1: a2);
          return;
        }
        v23 = v22 - 3;
        if ( v23 == 0 )
        {
          sub_46AD58(a1: a2);
          return;
        }
        v24 = v23 - 5;
        if ( v24 == 0 )
        {
          sub_46711F(a1: a2);
          return;
        }
        v25 = v24 - 2;
        if ( v25 == 0 )
        {
          sub_47112C();
          return;
        }
        if ( v25 == 2 )
        {
          sub_467180(a1: this);
          return;
        }
      }
      else
      {
        sub_A62490(a1: v26);
        v27 = 0;
        RecvPkt__DecodeBlob(this: a2, a2: (int)v26);
        sub_6A5A5E(a1: v26);
        v27 = -1;
        sub_A62530(a1: v26);
      }
    }
    else if ( v3 == 538 )
    {
      sub_47300E(a1: a2);
    }
    else if ( (unsigned __int16)v3 > 0x1F2u )
    {
      v18 = (unsigned __int16)v3 - 499;
      if ( v18 == 0 )
      {
        sub_467223(a1: a2);
        return;
      }
      v19 = v18 - 1;
      if ( v19 == 0 )
      {
        sub_467250(a1: a2);
        return;
      }
      if ( v19 == 1 )
        sub_46E347(a1: a2);
    }
    else
    {
      if ( v3 == 498 )
      {
        sub_467240(a1: a2);
        return;
      }
      v15 = (unsigned __int16)v3 - 289;
      if ( v15 == 0 )
      {
        sub_4658EF(a1: a2);
        return;
      }
      v16 = v15 - 35;
      if ( v16 == 0 )
      {
        sub_467382(a1: a2);
        return;
      }
      v17 = v16 - 73;
      if ( v17 == 0 )
      {
        sub_468750(a1: a2);
        return;
      }
      if ( v17 == 12 )
        sub_465912(a1: a2);
    }
  }
  else if ( (unsigned __int16)v3 == 253 )
  {
    sub_46D0A5(a1: a2);
  }
  else if ( (unsigned __int16)v3 > 0x74u )
  {
    v9 = (unsigned __int16)v3 - 117;
    if ( v9 != 0 )
    {
      v10 = v9 - 1;
      if ( v10 != 0 )
      {
        v11 = v10 - 1;
        if ( v11 != 0 )
        {
          v12 = v11 - 1;
          if ( v12 != 0 )
          {
            v13 = v12 - 1;
            if ( v13 != 0 )
            {
              v14 = v13 - 13;
              if ( v14 != 0 )
              {
                if ( v14 == 75 )
                {
                  sub_46E29C(a1: a2);
                  return;
                }
              }
              else
              {
                sub_46DC62(a1: a2);
              }
            }
            else
            {
              sub_472DBE(a1: a2);
            }
          }
          else
          {
            sub_470A99(a1: a2);
          }
        }
        else
        {
          sub_468504(a1: a2);
        }
      }
      else
      {
        sub_46A5D0(a1: a2);
      }
    }
    else
    {
      sub_476C92(a1: a2);
    }
  }
  else if ( v3 == 116 )
  {
    sub_4729D5(a1: a2);
  }
  else if ( (unsigned __int16)v3 > 0x6Fu )
  {
    v7 = (unsigned __int16)v3 - 113;
    if ( v7 != 0 )
    {
      v8 = v7 - 1;
      if ( v8 != 0 )
      {
        if ( v8 == 1 )
          sub_477F8B(a1: a2);
      }
      else
      {
        sub_470897(a1: a2);
      }
    }
    else
    {
      sub_46D2C7(a1: a2);
    }
  }
  else if ( v3 == 111 )
  {
    (*(void (__thiscall **)(void *, int *))(*(_DWORD *)this + 604))(a1: this, a2);
  }
  else
  {
    v4 = (unsigned __int16)v3 - 94;
    if ( v4 != 0 )
    {
      v5 = v4 - 12;
      if ( v5 != 0 )
      {
        v6 = v5 - 3;
        if ( v6 != 0 )
        {
          if ( v6 == 1 )
            (*(void (__thiscall **)(void *, int *))(*(_DWORD *)this + 588))(a1: this, a2);
        }
        else
        {
          (*(void (__thiscall **)(void *, int *))(*(_DWORD *)this + 584))(a1: this, a2);
        }
      }
      else
      {
        sub_475605(a1: a2);
      }
    }
    else
    {
      sub_471BAD(a1: a2);
    }
  }
  RecvPkt__Rewind(this: a2);
  CSessionStage__vf51(a1: a2);
  RecvPkt__Rewind(this: a2);
}