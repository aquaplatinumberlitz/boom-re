// CShopStageNew vf51 @ 0x806734
int __thiscall CShopStageNew__vf51(char *this, _DWORD *a2)
{
  int v3; // eax
  int v4; // eax
  int v5; // eax
  _DWORD *v6; // eax
  struct Concurrency::IExecutionContext *DefaultDestination; // eax
  int v8; // eax
  int v9; // eax
  int v10; // eax
  int v11; // eax
  int v12; // eax
  int v13; // eax
  _DWORD *v15; // [esp+10h] [ebp-40h]
  int v16[4]; // [esp+14h] [ebp-3Ch] BYREF
  _DWORD v17[10]; // [esp+24h] [ebp-2Ch] BYREF
  int v18; // [esp+4Ch] [ebp-4h]

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v3 > 0x101u )
  {
    v8 = (unsigned __int16)v3 - 335;
    if ( v8 == 0 )
    {
      sub_804B30(a1: a2);
      return sub_9DB5CB();
    }
    v9 = v8 - 20;
    if ( v9 != 0 )
    {
      v10 = v9 - 17;
      if ( v10 == 0 )
      {
        sub_7FFEE2(a1: a2);
        return sub_9DB5CB();
      }
      v11 = v10 - 46;
      if ( v11 == 0 )
      {
        sub_804707(a1: a2);
        return sub_9DB5CB();
      }
      v12 = v11 - 1;
      if ( v12 == 0 )
      {
        sub_804951(a1: a2);
        return sub_9DB5CB();
      }
      v13 = v12 - 80;
      if ( v13 == 0 )
      {
        sub_800A2A(a1: a2);
        return sub_9DB5CB();
      }
      if ( v13 == 5 )
      {
        sub_8B383D(a1: a2);
        return sub_9DB5CB();
      }
      goto LABEL_36;
    }
    sub_8BE76E(a1: a2);
    sub_7F40B1(a1: 0);
    if ( (unsigned __int8)sub_40176C(a1: 80) == 0 && dword_E64B04 != 0 )
      sub_91FAB3();
  }
  else
  {
    if ( (unsigned __int16)v3 == 257 )
    {
      sub_801744(a1: a2);
      return sub_9DB5CB();
    }
    if ( (unsigned __int16)v3 <= 0xD1u )
    {
      if ( v3 == 209 )
      {
        sub_800B9D(a1: a2);
        return sub_9DB5CB();
      }
      switch ( (unsigned __int16)v3 )
      {
        case 'I':
          CHiddenCatchPrepareStage__vf134(a1: a2);
          return sub_9DB5CB();
        case 'd':
          sub_8008D1(a1: a2);
          return sub_9DB5CB();
        case 'h':
          sub_800874(a1: a2);
          return sub_9DB5CB();
        case 'x':
          sub_801825(a1: a2);
          return sub_9DB5CB();
        default:
          break;
      }
LABEL_36:
      RecvPkt__Rewind(this: a2);
      CStage__vf51(a1: a2);
      return sub_9DB5CB();
    }
    v4 = (unsigned __int16)v3 - 223;
    if ( v4 != 0 )
    {
      v5 = v4 - 3;
      if ( v5 != 0 )
      {
        if ( v5 == 4 )
        {
          sub_805626(a1: a2);
          sub_8B4637(a1: dword_E6081C);
          return sub_9DB5CB();
        }
        goto LABEL_36;
      }
      sub_99D347(a1: v17);
      v18 = 0;
      v6 = (_DWORD *)v17[0];
      if ( v17[5] < 0x10u )
        v6 = v17;
      v15 = v6;
      DefaultDestination = Concurrency::details::UMSThreadVirtualProcessor::GetDefaultDestination(this: g_pMainWnd);
      sub_8AA343(a1: a2, a2: *((_DWORD *)this + 10982), a3: v15, a4: DefaultDestination);
      v18 = -1;
      std::string::_Tidy(a1: v17, a2: 1, Size: 0);
    }
    else
    {
      if ( dword_E61088 != 0 || (unsigned __int8)sub_40176C(a1: 80) == 0 && dword_E64B04 != 0 )
        goto LABEL_36;
      sub_803416(a1: a2);
      sub_800813();
      sub_8B4637(a1: dword_E6081C);
      if ( sub_8DAF28() == 0 )
      {
        sub_88849F(a1: 267);
        v18 = 1;
        SendPkt__EncodeBool(this: v16, a2: 2);
        SendPkt__EncodeBool(this: v16, a2: *(this + 43928));
        sub_8B3867(a1: *((_DWORD *)this + 10982));
        if ( (unsigned __int16)sub_8963D1(a1: v16) != 0 )
          sub_888609(a1: v16);
        sub_8B63D5(a1: *((void **)this + 10982));
        sub_8B56A4(a1: *((_DWORD *)this + 10982));
        v18 = -1;
        sub_8884DC();
      }
    }
  }
  return sub_9DB5CB();
}