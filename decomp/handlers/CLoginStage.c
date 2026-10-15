// CLoginStage vf51 @ 0x8544a2
int __stdcall CLoginStage__vf51(_DWORD *a1)
{
  unsigned __int16 v1; // ax
  int v2; // eax
  int v3; // eax
  int v4; // eax
  int v5; // eax
  int v6; // eax

  v1 = RecvPkt__Decode2(this: a1);
  if ( v1 > 0x10u )
  {
    v5 = v1 - 48;
    if ( v5 != 0 )
    {
      v6 = v5 - 1;
      if ( v6 != 0 )
      {
        if ( v6 == 10 )
          sub_850CB9(a1);
      }
      else
      {
        sub_8519C5(a1);
      }
    }
    else
    {
      sub_84FD8F(a1);
    }
  }
  else if ( v1 == 16 )
  {
    sub_84FB9F(a1);
  }
  else
  {
    v2 = v1 - 4;
    if ( v2 != 0 )
    {
      v3 = v2 - 1;
      if ( v3 != 0 )
      {
        v4 = v3 - 1;
        if ( v4 != 0 )
        {
          if ( v4 == 9 )
            sub_84FE35(a1);
        }
        else
        {
          sub_85185F(a1);
        }
      }
      else
      {
        sub_8502E7(a1);
      }
    }
    else
    {
      sub_8534F3(a1);
    }
  }
  RecvPkt__Rewind(this: a1);
  return CStage__vf51(a1);
}