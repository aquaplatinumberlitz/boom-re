// CChattingStage vf51 @ 0x68f099
int __thiscall CChattingStage__vf51(Concurrency::details::SchedulerBase *this, _DWORD *a2)
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

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v3 <= 0x73u )
  {
    if ( (unsigned __int16)v3 == 115 )
    {
      sub_68E9D0(a1: a2);
    }
    else if ( (unsigned __int16)v3 > 0x6Du )
    {
      v7 = (unsigned __int16)v3 - 110;
      if ( v7 != 0 )
      {
        v8 = v7 - 1;
        if ( v8 != 0 )
        {
          v9 = v8 - 2;
          if ( v9 != 0 )
          {
            if ( v9 == 1 )
              sub_68C486(a1: a2);
          }
          else
          {
            sub_68B85D(a1: a2);
          }
        }
        else
        {
          sub_68AE64(a1: a2);
        }
      }
      else
      {
        (*(void (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 588))(a1: this, a2);
      }
    }
    else if ( v3 == 109 )
    {
      (*(void (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 584))(a1: this, a2);
    }
    else
    {
      v4 = (unsigned __int16)v3 - 7;
      if ( v4 != 0 )
      {
        v5 = v4 - 96;
        if ( v5 != 0 )
        {
          v6 = v5 - 1;
          if ( v6 != 0 )
          {
            if ( v6 == 2 )
              (*(void (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 600))(
                a1: this,
                a2);
          }
          else
          {
            (*(void (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 572))(
              a1: this,
              a2);
          }
        }
        else
        {
          (*(void (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 564))(
            a1: this,
            a2);
        }
      }
      else
      {
        sub_68BA6D(a1: a2);
      }
    }
    goto LABEL_37;
  }
  if ( (unsigned __int16)v3 <= 0x81u )
  {
    if ( v3 == 129 )
    {
      sub_68DE6B(a1: a2);
    }
    else
    {
      v10 = (unsigned __int16)v3 - 118;
      if ( v10 != 0 )
      {
        v11 = v10 - 1;
        if ( v11 != 0 )
        {
          v12 = v11 - 1;
          if ( v12 != 0 )
          {
            if ( v12 == 1 )
              sub_68B95F(a1: a2);
          }
          else
          {
            sub_68C688(a1: a2);
          }
        }
        else
        {
          sub_68AEFE(a1: a2);
        }
      }
      else
      {
        sub_68B503(a1: a2);
      }
    }
    goto LABEL_37;
  }
  v13 = (unsigned __int16)v3 - 209;
  if ( v13 == 0 )
    return sub_68B7B2(a1: a2);
  v14 = v13 - 1;
  if ( v14 == 0 )
    return (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 340))(
             a1: this,
             a2);
  if ( v14 != 79 )
  {
LABEL_37:
    RecvPkt__Rewind(this: a2);
    return CChatStage__OnPacket(this, a2);
  }
  return sub_6952A5(a1: a2);
}