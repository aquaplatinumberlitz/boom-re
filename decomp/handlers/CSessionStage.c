// CSessionStage vf51 @ 0x6914cd
int __thiscall CSessionStage__vf51(Concurrency::details::SchedulerBase *this, _DWORD *a2)
{
  unsigned int v3; // ecx
  unsigned int v4; // ecx
  unsigned int v5; // ecx
  unsigned int v6; // ecx
  unsigned int v7; // ecx
  unsigned int v9; // ecx
  unsigned int v10; // ecx
  unsigned int v11; // ecx
  int v12; // eax

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( v3 <= 0x8F )
  {
    if ( v3 == 143 )
      return sub_6908B6(a1: a2);
    v4 = v3 - 7;
    if ( v4 != 0 )
    {
      v5 = v4 - 74;
      if ( v5 == 0 )
        return sub_69098F(a1: a2);
      v6 = v5 - 22;
      if ( v6 == 0 )
        return (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 564))(
                 a1: this,
                 a2);
      v7 = v6 - 1;
      if ( v7 == 0 )
        return (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 572))(
                 a1: this,
                 a2);
      if ( v7 == 1 )
        return (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 576))(
                 a1: this,
                 a2);
    }
    else
    {
      sub_690A31(a1: a2);
    }
    goto LABEL_18;
  }
  v9 = v3 - 144;
  if ( v9 != 0 )
  {
    v10 = v9 - 68;
    if ( v10 != 0 )
    {
      v11 = v10 - 182;
      if ( v11 != 0 )
      {
        if ( v11 != 6 )
        {
LABEL_18:
          RecvPkt__Rewind(this: a2);
          return CChatStage__OnPacket(this, a2);
        }
        return sub_6913F1(a1: a2);
      }
      else
      {
        return sub_69084A(a1: a2);
      }
    }
    else
    {
      return sub_6908FD(a1: a2);
    }
  }
  else
  {
    v12 = sub_97C626(a1: a2);
    return sub_8E7608(a1: v12);
  }
}