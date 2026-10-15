// CExchangeStage vf51 @ 0x845cac
int __thiscall CExchangeStage__vf51(void *this, _DWORD *a2)
{
  int v3; // eax
  int v4; // eax
  int v5; // eax
  int v6; // eax
  int v8; // eax
  int v9; // eax
  int v10; // eax
  int v11; // eax
  int v12; // eax
  int v13; // eax
  int v14; // eax
  int v15; // eax

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v3 > 0x77u )
  {
    v10 = (unsigned __int16)v3 - 120;
    if ( v10 != 0 )
    {
      v11 = v10 - 16;
      if ( v11 != 0 )
      {
        v12 = v11 - 1;
        if ( v12 != 0 )
        {
          v13 = v12 - 1;
          if ( v13 != 0 )
          {
            v14 = v13 - 1;
            if ( v14 != 0 )
            {
              v15 = v14 - 1;
              if ( v15 == 0 )
                return sub_8418A2(a1: a2);
              if ( v15 == 254 )
                return sub_69084A(a1: a2);
            }
            else
            {
              sub_8415CA(a1: a2);
            }
          }
          else
          {
            sub_83FE24(a1: a2);
          }
        }
        else
        {
          sub_8453CB(a1: a2);
        }
      }
      else
      {
        sub_845C5A(a1: a2);
      }
    }
    else
    {
      sub_843318(a1: a2);
    }
  }
  else if ( (unsigned __int16)v3 == 119 )
  {
    sub_840370(a1: a2);
  }
  else if ( (unsigned __int16)v3 > 0x6Au )
  {
    v8 = (unsigned __int16)v3 - 109;
    if ( v8 != 0 )
    {
      v9 = v8 - 1;
      if ( v9 != 0 )
      {
        if ( v9 == 8 )
          sub_841471(a1: a2);
      }
      else
      {
        (*(void (__thiscall **)(void *, _DWORD *))(*(_DWORD *)this + 588))(a1: this, a2);
      }
    }
    else
    {
      (*(void (__thiscall **)(void *, _DWORD *))(*(_DWORD *)this + 584))(a1: this, a2);
    }
  }
  else if ( v3 == 106 )
  {
    (*(void (__thiscall **)(void *, _DWORD *))(*(_DWORD *)this + 600))(a1: this, a2);
  }
  else
  {
    v4 = (unsigned __int16)v3 - 7;
    if ( v4 == 0 )
      return sub_690A31(a1: a2);
    v5 = v4 - 27;
    if ( v5 == 0 )
      return sub_84192A(a1: a2);
    v6 = v5 - 69;
    if ( v6 == 0 )
      return (*(int (__thiscall **)(void *, _DWORD *))(*(_DWORD *)this + 564))(a1: this, a2);
    if ( v6 == 1 )
      return (*(int (__thiscall **)(void *, _DWORD *))(*(_DWORD *)this + 572))(a1: this, a2);
  }
  RecvPkt__Rewind(this: a2);
  return CSessionStage__vf51(a1: a2);
}