// CHiddenCatchSinglePrepareStage vf51 @ 0x4b2e47
void __thiscall CHiddenCatchSinglePrepareStage__vf51(void *this, int *a2)
{
  int v3; // eax
  int v4; // eax
  int v5; // eax
  int v6; // eax

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2) - 223;
  if ( v3 == 0 )
  {
LABEL_9:
    sub_4B4432(a1: a2);
    goto LABEL_10;
  }
  v4 = v3 - 376;
  if ( v4 == 0 )
  {
    sub_4B2933(a1: a2);
    return;
  }
  v5 = v4 - 5;
  if ( v5 != 0 )
  {
    v6 = v5 - 3;
    if ( v6 != 0 )
    {
      if ( v6 == 3 )
        sub_4B2902(a1: a2);
      goto LABEL_10;
    }
    goto LABEL_9;
  }
  sub_4B2ADF(a1: a2);
LABEL_10:
  RecvPkt__Rewind(this: a2);
  CHiddenCatchPrepareStage__OnPacket(this, a2);
  RecvPkt__Rewind(this: a2);
}