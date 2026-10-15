// CSelectServerStage vf51 @ 0x859c70
int __stdcall CSelectServerStage__vf51(_DWORD *a1)
{
  int v1; // eax
  int v2; // eax
  int v3; // eax
  int result; // eax
  int v5; // eax
  int v6; // eax

  v1 = (unsigned __int16)RecvPkt__Decode2(this: a1) - 7;
  if ( v1 == 0 )
    return sub_8558C4(a1);
  v2 = v1 - 9;
  if ( v2 == 0 )
    return sub_854ADC(a1);
  v3 = v2 - 3;
  if ( v3 == 0 )
    return sub_855F5B(a1);
  result = v3 - 1;
  if ( result != 0 )
  {
    v5 = result - 21;
    if ( v5 != 0 )
    {
      v6 = v5 - 22;
      if ( v6 == 0 || (result = v6 - 346) != 0 )
      {
        RecvPkt__Rewind(this: a1);
        return CStage__vf51(a1);
      }
    }
    else
    {
      sub_65786B(a1);
      return sub_859375();
    }
  }
  return result;
}