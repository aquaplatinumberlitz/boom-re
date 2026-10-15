// CMagicBookMarketStage vf51 @ 0x880a2f
int __thiscall CMagicBookMarketStage__vf51(_DWORD *this, _DWORD *a2)
{
  unsigned int v3; // ecx
  unsigned int v4; // ecx
  unsigned int v5; // ecx
  unsigned int v6; // ecx
  _DWORD *v7; // eax
  struct Concurrency::IExecutionContext *DefaultDestination; // eax
  unsigned int v9; // ecx
  unsigned int v10; // ecx
  unsigned int v11; // ecx
  _DWORD *v13; // [esp+10h] [ebp-30h]
  _DWORD v14[10]; // [esp+14h] [ebp-2Ch] BYREF
  int v15; // [esp+3Ch] [ebp-4h]

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( v3 > 0x1A6 )
  {
    v9 = v3 - 423;
    if ( v9 == 0 )
    {
      sub_8802E4(a1: a2);
      return sub_9DB5CB();
    }
    v10 = v9 - 2;
    if ( v10 == 0 )
    {
      sub_8804F3(a1: a2);
      return sub_9DB5CB();
    }
    v11 = v10 - 1;
    if ( v11 == 0 )
    {
      sub_88087F(a1: a2);
      return sub_9DB5CB();
    }
    if ( v11 == 73 )
    {
      sub_87FF12(a1: a2);
      return sub_9DB5CB();
    }
    goto LABEL_18;
  }
  if ( v3 == 422 )
  {
    sub_880221(a1: a2);
    return sub_9DB5CB();
  }
  v4 = v3 - 100;
  if ( v4 == 0 )
  {
    sub_87FEF7(a1: a2);
    return sub_9DB5CB();
  }
  v5 = v4 - 126;
  if ( v5 != 0 )
  {
    v6 = v5 - 4;
    if ( v6 == 0 )
    {
      sub_805626(a1: a2);
      return sub_9DB5CB();
    }
    if ( v6 == 59 )
    {
      sub_87FB3F(a1: a2);
      return sub_9DB5CB();
    }
LABEL_18:
    RecvPkt__Rewind(this: a2);
    CStage__vf51(a1: a2);
    return sub_9DB5CB();
  }
  sub_99D347(a1: v14);
  v15 = 0;
  v7 = (_DWORD *)v14[0];
  if ( v14[5] < 0x10u )
    v7 = v14;
  v13 = v7;
  DefaultDestination = Concurrency::details::UMSThreadVirtualProcessor::GetDefaultDestination(this: g_pMainWnd);
  sub_8AA343(a1: a2, a2: *(this + 10982), a3: v13, a4: DefaultDestination);
  v15 = -1;
  std::string::_Tidy(a1: v14, a2: 1, Size: 0);
  return sub_9DB5CB();
}