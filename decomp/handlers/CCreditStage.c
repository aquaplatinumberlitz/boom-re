// CCreditStage vf51 @ 0x68f26a
int __thiscall CCreditStage__vf51(void *this, _DWORD *a2)
{
  if ( (unsigned __int16)RecvPkt__Decode2(this: a2) == 7 )
    return sub_68F252(a1: this);
  RecvPkt__Rewind(this: a2);
  return CStage__vf51(a1: a2);
}