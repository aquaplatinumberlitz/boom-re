// CLobbySquareStage vf51 @ 0x4e5a38
int __thiscall CLobbySquareStage__vf51(Concurrency::details::SchedulerBase *this, _DWORD *a2)
{
  int v3; // eax
  int v4; // eax
  int v5; // eax
  int v6; // eax
  int v7; // eax
  int v8; // eax
  int result; // eax
  int v10; // eax
  int v11; // eax
  int v12; // eax
  int v13; // eax

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v3 > 0x1E2u )
  {
    if ( (unsigned __int16)v3 > 0x240u )
    {
      switch ( (__int16)v3 )
      {
        case 612:
          sub_4DE0C0(a1: a2);
          goto LABEL_75;
        case 613:
          result = sub_4E36D2(a1: a2);
          break;
        case 614:
          sub_4D9C6F(a1: a2);
          goto LABEL_75;
        case 615:
          sub_4D5E7B(a1: a2);
          goto LABEL_75;
        case 616:
          sub_4D9D56(a1: a2);
          goto LABEL_75;
        case 617:
          sub_4D5E89(a1: a2);
          goto LABEL_75;
        case 622:
          sub_4BCB30(a1: a2);
          goto LABEL_75;
        case 623:
          sub_4BCB79(a1: a2);
          goto LABEL_75;
        case 624:
          sub_4BCC41(a1: a2);
          goto LABEL_75;
        case 625:
          sub_4BCB8F(a1: a2);
          goto LABEL_75;
        default:
          goto LABEL_75;
      }
    }
    else if ( v3 == 576 )
    {
      return sub_4D6E91(a1: a2);
    }
    else
    {
      switch ( (__int16)v3 )
      {
        case 483:
          result = sub_4DC4B0(a1: a2);
          break;
        case 484:
          result = sub_4D5BD1(a1: a2);
          break;
        case 485:
          result = sub_4D93A8(a1: a2);
          break;
        case 486:
          result = sub_4DFC08(a1: a2);
          break;
        case 487:
          result = sub_4DF224(a1: a2);
          break;
        case 488:
          result = sub_4DF798(a1: a2);
          break;
        case 489:
          result = sub_4DF238(a1: a2);
          break;
        case 492:
          result = sub_4E242D(a1: a2);
          break;
        case 493:
          result = sub_4D92F2(a1: a2);
          break;
        case 496:
          result = sub_4DAF64(a1: a2);
          break;
        case 506:
          result = (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 232))(
                     a1: this,
                     a2);
          break;
        case 507:
          result = sub_4DDB1E(a1: a2);
          break;
        case 508:
          result = sub_4DDBC5(a1: a2);
          break;
        default:
          goto LABEL_75;
      }
    }
  }
  else if ( (unsigned __int16)v3 == 482 )
  {
    return sub_4DC39E(a1: a2);
  }
  else if ( (unsigned __int16)v3 > 0x1D5u )
  {
    result = (unsigned __int16)v3 - 470;
    switch ( result )
    {
      case 0:
        result = sub_4DA834(a1: a2);
        break;
      case 1:
        result = sub_4D8E98(a1: a2);
        break;
      case 2:
        result = sub_4D8F32(a1: a2);
        break;
      case 3:
        result = sub_4DA862(a1: a2);
        break;
      case 4:
        result = sub_4E26BB(a1: a2);
        break;
      case 5:
        result = sub_4DF1F8(a1: a2);
        break;
      case 6:
        result = sub_4DAC78(a1: a2);
        break;
      case 7:
        result = sub_4D9060(a1: a2);
        break;
      case 8:
        result = sub_4D90F5(a1: a2);
        break;
      case 9:
        return result;
      case 10:
        result = sub_4E14B1(a1: a2);
        break;
      case 11:
        result = sub_4DA8E7(a1: a2);
        break;
      default:
        goto LABEL_75;
    }
  }
  else if ( v3 == 469 )
  {
    return sub_4E36B1(a1: a2);
  }
  else
  {
    if ( (unsigned __int16)v3 > 0x121u )
    {
      v10 = (unsigned __int16)v3 - 394;
      if ( v10 != 0 )
      {
        v11 = v10 - 25;
        if ( v11 == 0 )
          return sub_4E0FB7(a1: a2);
        v12 = v11 - 7;
        if ( v12 == 0 )
          return sub_4E119C(a1: a2);
        v13 = v12 - 40;
        if ( v13 == 0 )
          return sub_4E52B5(a1: a2);
        if ( v13 == 1 )
          return sub_4E4100(a1: a2);
      }
      else
      {
        result = sub_4DF9A8(a1: a2);
        if ( result == 0 )
          return result;
      }
    }
    else
    {
      if ( v3 == 289 )
        return sub_4D5BAE(a1: a2);
      v4 = (unsigned __int16)v3 - 26;
      if ( v4 != 0 )
      {
        v5 = v4 - 1;
        if ( v5 != 0 )
        {
          v6 = v5 - 5;
          if ( v6 == 0 )
            return (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 240))(
                     a1: this,
                     a2);
          v7 = v6 - 47;
          if ( v7 == 0 )
            return sub_4DAD83(a1: a2);
          v8 = v7 - 155;
          if ( v8 == 0 )
            return sub_4DBC0D(a1: a2);
          if ( v8 == 31 )
            return sub_4DEA21(a1: a2);
        }
        else if ( sub_9B6F75(a1: 7) == 0 )
        {
          sub_4E0D5B(a1: a2);
        }
      }
      else if ( sub_9B6F75(a1: 7) == 0 )
      {
        sub_4E061B(a1: a2);
      }
    }
LABEL_75:
    sub_42DA98(a1: a2);
    RecvPkt__Rewind(this: a2);
    sub_4D24BB(a1: a2);
    RecvPkt__Rewind(this: a2);
    sub_4D39EB(a1: a2);
    RecvPkt__Rewind(this: a2);
    sub_4C011B(a1: a2);
    RecvPkt__Rewind(this: a2);
    return CChatStage__OnPacket(this, a2);
  }
  return result;
}