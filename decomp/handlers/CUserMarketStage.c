// CUserMarketStage vf51 @ 0x8603a3
int __thiscall CUserMarketStage__vf51(_DWORD *this, int *a2)
{
  unsigned int v3; // ecx
  unsigned int v4; // ecx
  unsigned int v5; // ecx
  unsigned int v6; // ecx
  unsigned int v7; // ecx
  unsigned int v8; // ecx
  unsigned int v9; // ecx
  unsigned int v11; // ecx
  unsigned int v12; // ecx
  unsigned int v13; // ecx
  unsigned int v14; // ecx
  unsigned int v15; // ecx

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( v3 <= 0x19F )
  {
    if ( v3 == 415 )
      return sub_85D6CE(a1: a2);
    v4 = v3 - 100;
    if ( v4 == 0 )
      return sub_85E71A(a1: a2);
    v5 = v4 - 189;
    if ( v5 == 0 )
      return sub_85E453(a1: a2);
    v6 = v5 - 121;
    if ( v6 == 0 )
      return sub_85E9BE(a1: a2);
    v7 = v6 - 1;
    if ( v7 == 0 )
      return sub_85E99F(a1: a2);
    v8 = v7 - 1;
    if ( v8 == 0 )
      return sub_85E472(a1: a2);
    v9 = v8 - 1;
    if ( v9 == 0 )
      return sub_85F5BA(a1: a2);
    if ( v9 == 1 )
      return sub_85F7E2(a1: a2);
    goto LABEL_24;
  }
  v11 = v3 - 416;
  if ( v11 == 0 )
    return sub_85F960(a1: a2);
  v12 = v11 - 1;
  if ( v12 == 0 )
    return sub_85FA25(a1: a2);
  v13 = v12 - 1;
  if ( v13 == 0 )
    return sub_804707(a1: a2);
  v14 = v13 - 1;
  if ( v14 == 0 )
    return sub_804951(a1: a2);
  v15 = v14 - 1;
  if ( v15 == 0 )
    return sub_85E481(a1: a2);
  if ( v15 != 79 )
  {
LABEL_24:
    RecvPkt__Rewind(this: a2);
    return CStage__OnPacket(this, a2);
  }
  return sub_85E853(a1: a2);
}