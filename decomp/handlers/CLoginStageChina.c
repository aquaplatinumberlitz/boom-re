// CLoginStageChina vf51 @ 0x84f313
int __thiscall CLoginStageChina__vf51(_DWORD *this, _DWORD *a2)
{
  unsigned __int16 v3; // ax
  int v4; // eax
  int v5; // eax
  int v6; // eax
  int v7; // eax
  int v8; // eax
  int v10; // eax
  int v11; // eax
  int v12; // eax
  int v13; // eax

  v3 = RecvPkt__Decode2(this: a2);
  if ( v3 > 0x36u )
  {
    v10 = v3 - 55;
    if ( v10 != 0 )
    {
      v11 = v10 - 1;
      if ( v11 != 0 )
      {
        v12 = v11 - 1;
        if ( v12 == 0 )
          return sub_84B1F4(a1: a2);
        v13 = v12 - 1;
        if ( v13 == 0 )
          return sub_84A924(a1: a2);
        if ( v13 == 4 )
          return sub_84A959(a1: a2);
      }
      else
      {
        sub_84C590(a1: a2);
      }
    }
    else
    {
      sub_84C020(a1: a2);
    }
  }
  else if ( v3 == 54 )
  {
    sub_84BE43(a1: a2);
  }
  else
  {
    v4 = v3 - 4;
    if ( v4 != 0 )
    {
      v5 = v4 - 1;
      if ( v5 != 0 )
      {
        v6 = v5 - 1;
        if ( v6 != 0 )
        {
          v7 = v6 - 9;
          if ( v7 != 0 )
          {
            v8 = v7 - 1;
            if ( v8 != 0 )
            {
              if ( v8 == 37 )
                return sub_84C390(a1: a2);
            }
            else
            {
              sub_84AC44(a1: a2);
            }
          }
          else
          {
            sub_84B3B7(a1: a2);
          }
        }
        else
        {
          sub_84B99A(a1: a2);
        }
      }
      else
      {
        sub_84B816(a1: a2);
      }
    }
    else
    {
      sub_84DE0E(a1: a2);
    }
  }
  if ( *(this + 11952) != 0 )
  {
    RecvPkt__Rewind(this: a2);
    sub_84A3F6(a1: a2);
  }
  RecvPkt__Rewind(this: a2);
  return CStage__vf51(a1: a2);
}