// CSquareStage vf51 @ 0x86ff2c
int __thiscall CSquareStage__vf51(Concurrency::details::SchedulerBase *this, _DWORD *a2)
{
  int v3; // ebx
  int result; // eax
  int v5; // ebx

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned int)v3 > 0x1E1 )
  {
    switch ( v3 )
    {
      case 482:
        result = sub_86A88A(a1: a2);
        break;
      case 483:
        result = sub_86A99C(a1: a2);
        break;
      case 484:
        result = sub_86794B(a1: a2);
        break;
      case 485:
        result = sub_868369(a1: a2);
        break;
      case 486:
        result = sub_86D746(a1: a2);
        break;
      case 487:
        result = sub_86CD83(a1: a2);
        break;
      case 488:
        result = sub_86D2F7(a1: a2);
        break;
      case 489:
        result = sub_86CD97(a1: a2);
        break;
      case 490:
        result = sub_86BCD6(a1: a2);
        break;
      case 492:
        result = sub_86F07F(a1: a2);
        break;
      case 493:
        result = sub_8678E3(a1: a2);
        break;
      case 496:
        result = sub_869E16(a1: a2);
        break;
      case 506:
        result = (*(int (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 232))(
                   a1: this,
                   a2);
        break;
      case 507:
        result = sub_86C33F(a1: a2);
        break;
      case 508:
        result = sub_86C3E6(a1: a2);
        break;
      case 509:
        result = sub_86799F(a1: a2);
        break;
      case 510:
        result = sub_8684B1(a1: a2);
        break;
      case 511:
        result = sub_868516(a1: a2);
        break;
      case 512:
        result = sub_8679BC(a1: a2);
        break;
      default:
        goto LABEL_18;
    }
  }
  else if ( v3 == 481 )
  {
    return sub_8698DE(a1: a2);
  }
  else if ( v3 > 471 )
  {
    result = v3 - 472;
    switch ( v3 )
    {
      case 472:
        result = sub_8677D0(a1: a2);
        break;
      case 473:
        result = sub_869844(a1: a2);
        break;
      case 474:
        result = sub_86F7F6(a1: a2);
        break;
      case 475:
        result = sub_86CD57(a1: a2);
        break;
      case 476:
        result = sub_869CBD(a1: a2);
        break;
      case 477:
        result = sub_867873(a1: a2);
        break;
      case 478:
        result = sub_868676(a1: a2);
        break;
      case 479:
        return result;
      case 480:
        result = sub_86E9C0(a1: a2);
        break;
    }
  }
  else if ( v3 == 471 )
  {
    return sub_867731(a1: a2);
  }
  else
  {
    if ( v3 > 394 )
    {
      switch ( v3 )
      {
        case 466:
          return sub_869BAD(a1: a2);
        case 467:
          return sub_86FE10(a1: a2);
        case 469:
          return sub_86F7D5(a1: a2);
        case 470:
          return sub_86A7B4(a1: a2);
        default:
          break;
      }
    }
    else
    {
      switch ( v3 )
      {
        case 394:
          result = sub_86D4CD(a1: a2);
          if ( result == 0 )
            return result;
          break;
        case 16:
          return sub_8680B0(a1: a2);
        case 83:
          return sub_86B66A(a1: a2);
        case 84:
          return sub_86BDE7(a1: a2);
        case 234:
          return sub_867E32(a1: a2);
        case 289:
          return sub_867928(a1: a2);
        default:
          break;
      }
    }
LABEL_18:
    RecvPkt__Rewind(this: a2);
    CChatStage__OnPacket(this, a2);
    v5 = v3 - 67;
    if ( v5 != 0 )
    {
      if ( v5 == 2 )
      {
        return sub_868E4E(a1: this);
      }
      else
      {
        result = sub_40176C(a1: 6);
        if ( (_BYTE)result == 0 )
        {
          result = sub_A65990(this: a2);
          if ( (_WORD)result == 434 )
            return (*(int (__thiscall **)(_DWORD *, int))(*((_DWORD *)this + 36) + 20))(
                     a1: (_DWORD *)this + 36,
                     a2: 6005);
        }
      }
    }
    else
    {
      return sub_868F08(a1: this);
    }
  }
  return result;
}