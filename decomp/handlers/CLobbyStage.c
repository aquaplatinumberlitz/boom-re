// CLobbyStage vf51 @ 0x6b2ed4
int __thiscall CLobbyStage__vf51(Concurrency::details::SchedulerBase *this, int *a2)
{
  int v3; // ebx
  int result; // eax
  int v5; // ebx
  int v6; // edi
  int i; // esi
  int v8; // eax
  _BYTE v9[36]; // [esp+10h] [ebp-28h] BYREF
  int v10; // [esp+34h] [ebp-4h]

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned int)v3 > 0x16B )
  {
    if ( v3 > 426 )
    {
      switch ( v3 )
      {
        case 499:
          return sub_6AE72A(a1: a2);
        case 505:
          sub_6B011E(a1: a2);
          break;
        case 553:
          if ( (unsigned __int8)sub_40176C(a1: 47) == 0 && sub_8DACD5() != 0 )
          {
            sub_A62490(a1: v9);
            v10 = 0;
            RecvPkt__DecodeBlob(this: a2, a2: (int)v9);
            sub_6A5A5E(a1: v9);
            v10 = -1;
            return sub_A62530(a1: v9);
          }
          break;
        case 554:
          return sub_6AE817(a1: a2);
        case 576:
          return sub_6AE836(a1: a2);
        default:
          break;
      }
    }
    else
    {
      switch ( v3 )
      {
        case 426:
          return sub_6B2433(a1: a2);
        case 368:
          return sub_6AE770(a1: a2);
        case 372:
          return sub_6ADFAD(a1: a2);
        case 406:
          return sub_6AEF18(a1: a2);
        case 418:
          return sub_6B1FEC(a1: a2);
        case 419:
          return sub_6B224E(a1: a2);
        default:
          break;
      }
    }
    goto LABEL_58;
  }
  if ( v3 == 363 )
    return sub_6ADF1C(a1: a2);
  if ( v3 > 125 )
  {
    switch ( v3 )
    {
      case 259:
        return sub_6B27BB(a1: a2);
      case 265:
        sub_6B147E(a1: a2);
        break;
      case 268:
        return sub_6B25E3(a1: a2);
      case 289:
        return (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, int *))(*(_DWORD *)this + 568))(
                 a1: this,
                 a2);
      default:
        break;
    }
    goto LABEL_58;
  }
  switch ( v3 )
  {
    case 125:
      if ( (unsigned __int8)sub_40176C(a1: 47) == 0 && sub_8DACD5() != 0 )
        return sub_6B1358(a1: a2);
      goto LABEL_58;
    case 7:
      sub_6AFEDF(a1: a2);
LABEL_58:
      RecvPkt__Rewind(this: a2);
      sub_4D24BB(a1: a2);
      RecvPkt__Rewind(this: a2);
      sub_512B66(a1: a2);
      RecvPkt__Rewind(this: a2);
      result = CChatStage__OnPacket(this, a2);
      v5 = v3 - 218;
      if ( v5 != 0 )
      {
        if ( v5 == 16 )
          return sub_6B0D7C();
      }
      else
      {
        result = sub_99AEE3(a1: dword_E60880);
        v6 = result;
        for ( i = 0; i < v6; ++i )
        {
          result = sub_8B4DBE(a1: i, a2: 4, a3: 0);
          if ( result != 0 )
          {
            v8 = sub_414543(a1: result + 60);
            result = sub_5AC7F8(a1: v8, a2: 1);
          }
        }
      }
      return result;
    case 19:
      return sub_6B0357(a1: a2);
    case 26:
      if ( sub_9B6F75(a1: 7) == 0 )
        sub_6B167A(a1: a2);
      goto LABEL_58;
    case 32:
      return (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, int *))(*(_DWORD *)this + 240))(a1: this, a2);
    default:
      break;
  }
  if ( v3 != 89 )
  {
    if ( v3 == 124 && (unsigned __int8)sub_40176C(a1: 47) == 0 && sub_8DACD5() != 0 )
      return sub_6B12D3(a1: a2);
    goto LABEL_58;
  }
  result = sub_40176C(a1: 47);
  if ( (_BYTE)result == 0 )
  {
    result = sub_8DACD5();
    if ( result != 0 )
      return sub_6AEB4A(a1: this, a2);
  }
  return result;
}