// CGameStage vf51 @ 0x71b631
int __thiscall CGameStage__vf51(_DWORD *this, _DWORD *a2)
{
  int v4; // eax
  int result; // eax
  unsigned __int8 v6; // al
  int v7; // eax
  int v8; // eax
  int v9; // eax
  int v10; // eax
  int v11; // eax
  int v12; // eax
  int v13; // eax
  int v14; // eax
  int v15; // eax
  int v16; // eax
  int v17; // eax
  int v18; // eax
  unsigned __int8 v19; // al
  int v20; // eax
  int v21; // eax
  int v22; // eax
  int v23; // eax
  _DWORD *v24; // eax
  _DWORD *v25; // ebx
  _BYTE v26[36]; // [esp+10h] [ebp-28h] BYREF
  int v27; // [esp+34h] [ebp-4h]
  void *v28; // [esp+40h] [ebp+8h]

  v4 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v4 <= 0xD6u )
  {
    if ( (unsigned __int16)v4 == 214 )
      return sub_70DD0E(a1: a2);
    result = (unsigned __int16)v4 - 20;
    switch ( result )
    {
      case 0:
        return result;
      case 5:
        if ( sub_8DE182(a1: dword_E60928) == 0 )
          sub_7127B3(a1: a2);
        goto LABEL_138;
      case 61:
        sub_70C8C1(a1: a2);
        goto LABEL_138;
      case 86:
        result = sub_7019AE(a1: a2);
        break;
      case 87:
        sub_703D01(a1: a2);
        goto LABEL_138;
      case 99:
        (*(void (__thiscall **)(_DWORD *, _DWORD *))(*this + 592))(a1: this, a2);
        goto LABEL_138;
      case 108:
        result = sub_71458E(a1: a2);
        break;
      case 115:
        v6 = RecvPkt__Decode1(this: a2);
        sub_9B5934(a1: v6);
        if ( sub_9B6F75(a1: 4) != 0 )
        {
          *(this + 5535) = 1;
          sub_6FFBD4(a1: 5);
        }
        goto LABEL_138;
      case 125:
        result = sub_701A48(a1: a2);
        break;
      case 126:
        result = sub_70DE4C(a1: a2);
        break;
      case 127:
        sub_701AB1(a1: a2);
        goto LABEL_138;
      case 128:
        result = sub_704CD8(a1: a2);
        break;
      case 129:
        result = sub_704D77(a1: a2);
        break;
      case 130:
        result = sub_6FFF78(a1: a2);
        break;
      case 131:
        sub_70205B(a1: a2);
        goto LABEL_138;
      case 132:
        sub_7064AC(a1: a2);
        goto LABEL_138;
      case 133:
        sub_70679A(a1: a2);
        goto LABEL_138;
      case 135:
        sub_701E8B(a1: a2);
        goto LABEL_138;
      case 137:
        sub_7068DE(a1: a2);
        goto LABEL_138;
      case 138:
        sub_715E90(a1: a2, a2: 0);
        goto LABEL_138;
      case 139:
        result = sub_703F52();
        break;
      case 140:
        sub_7164BB(a1: a2);
        goto LABEL_138;
      case 141:
        sub_704962(a1: a2);
        goto LABEL_138;
      case 143:
        sub_716735(a1: a2);
        goto LABEL_138;
      case 144:
        sub_701765(a1: a2);
        goto LABEL_138;
      case 145:
        result = sub_7018D7(a1: a2);
        break;
      case 146:
        sub_708EB0(a1: a2);
        goto LABEL_138;
      case 148:
        result = sub_719D08(a1: a2);
        break;
      case 149:
        result = sub_7090AD(a1: a2);
        break;
      case 150:
        result = sub_70FF80(a1: a2);
        break;
      case 151:
        result = sub_7069DF(a1: a2);
        break;
      case 153:
        if ( sub_8DB058() != 0 )
          result = sub_708FFE(a1: 0, a2: 0);
        else
          result = (*(int (__thiscall **)(_DWORD *, _DWORD *))(*this + 596))(a1: this, a2);
        break;
      case 154:
        result = sub_70264F(a1: a2);
        break;
      case 156:
        result = sub_706C42(a1: a2);
        break;
      case 157:
        result = sub_706D3C(a1: a2);
        break;
      case 158:
        result = sub_7150E7(a1: a2);
        break;
      case 164:
        sub_709101(a1: a2);
        goto LABEL_138;
      case 169:
        result = sub_70E5C4(a1: a2);
        break;
      case 170:
        result = sub_70E7D6(a1: a2);
        break;
      case 171:
        result = sub_709A38(a1: a2);
        break;
      case 172:
        result = sub_7173A5(a1: a2);
        break;
      case 173:
        result = sub_715210(a1: a2);
        break;
      case 174:
        result = sub_706823(a1: a2);
        break;
      case 175:
        sub_701D15(a1: a2);
        goto LABEL_138;
      case 176:
        result = sub_707101(a1: a2);
        break;
      case 184:
        result = sub_7071AC(a1: a2);
        break;
      case 185:
        sub_701B11(a1: a2);
        goto LABEL_138;
      case 189:
        result = sub_70EE54(a1: a2);
        break;
      default:
        goto LABEL_138;
    }
    return result;
  }
  if ( (unsigned __int16)v4 > 0x205u )
  {
    result = (unsigned __int16)v4 - 518;
    switch ( result )
    {
      case 0:
        result = sub_70F7A3(a1: a2);
        break;
      case 1:
        result = sub_70054E(a1: a2);
        break;
      case 5:
        result = sub_717B87(a1: a2);
        break;
      case 8:
        result = sub_711B3A(a1: a2);
        break;
      case 11:
        if ( *(this + 5395) != 0 )
        {
          result = sub_6FA585();
          if ( result == 0 )
            result = sub_6FC976(a1: 39, a2: 371, a3: this);
        }
        break;
      case 13:
        result = sub_70A158(a1: a2);
        break;
      case 14:
        result = sub_70A04B(a1: a2);
        break;
      case 18:
        result = sub_70FC1B(a1: a2);
        break;
      case 20:
        result = sub_703951(a1: a2);
        break;
      case 21:
        result = sub_71798F(a1: a2);
        break;
      case 22:
        result = sub_703921(a1: a2);
        break;
      case 27:
        result = sub_717EFC(a1: a2);
        break;
      case 29:
        result = sub_707E78(a1: a2);
        break;
      case 30:
        result = sub_71824D(a1: a2);
        break;
      case 34:
        result = sub_71580C(a1: a2);
        break;
      case 35:
        sub_A62490(a1: v26);
        v27 = 0;
        RecvPkt__DecodeBlob(this: a2, a2: (int)v26);
        sub_6A5A5E(a1: v26);
        v27 = -1;
        sub_A62530(a1: v26);
        goto LABEL_138;
      case 37:
        result = sub_703A20(a1: a2);
        break;
      case 50:
        result = sub_705016(a1: a2);
        break;
      case 51:
        result = sub_7038CD(a1: a2);
        break;
      case 52:
        result = sub_70C70D(a1: a2);
        break;
      case 53:
        result = sub_71ADEC(a1: a2);
        break;
      case 54:
        result = sub_709D5E(a1: a2);
        break;
      case 60:
        sub_70065D(a1: a2);
        goto LABEL_138;
      default:
        goto LABEL_138;
    }
  }
  else
  {
    if ( v4 == 517 )
      return sub_717791(a1: a2);
    if ( (unsigned __int16)v4 <= 0x164u )
    {
      if ( v4 == 356 )
        return sub_7155DA(a1: a2);
      if ( (unsigned __int16)v4 > 0x138u )
      {
        v12 = (unsigned __int16)v4 - 313;
        if ( v12 == 0 )
          return sub_707D14(a1: a2);
        v13 = v12 - 1;
        if ( v13 == 0 )
          return sub_7101FA(a1: a2);
        v14 = v13 - 1;
        if ( v14 == 0 )
          return sub_7158EC(a1: a2);
        v15 = v14 - 9;
        if ( v15 == 0 )
          return sub_703E0C(a1: a2);
        if ( v15 == 15 )
          return sub_7100B2(a1: a2);
      }
      else
      {
        if ( v4 == 312 )
          return sub_70AF9C(a1: a2);
        v7 = (unsigned __int16)v4 - 215;
        if ( v7 == 0 )
          return sub_7129C4(a1: a2);
        v8 = v7 - 1;
        if ( v8 == 0 )
          return sub_70DDB4(a1: a2);
        v9 = v8 - 51;
        if ( v9 == 0 )
          return sub_69BABE(a1: a2);
        v10 = v9 - 31;
        if ( v10 == 0 )
          return sub_7035C4(a1: a2);
        v11 = v10 - 5;
        if ( v11 == 0 )
          return sub_70727E(a1: a2);
        if ( v11 == 8 )
          return sub_719A3C(a1: a2);
      }
LABEL_138:
      if ( *(this + 5417) == 0
        || (RecvPkt__Rewind(this: a2),
            (result = (*(int (__thiscall **)(_DWORD, _DWORD *))(*(_DWORD *)*(this + 5417) + 48))(a1: *(this + 5417), a2)) == 0) )
      {
        RecvPkt__Rewind(this: a2);
        sub_8883BE(a1: a2);
        v24 = (_DWORD *)*(this + 5413);
        v25 = (_DWORD *)*v24;
        if ( (_DWORD *)*v24 != v24 )
        {
          do
          {
            v28 = (void *)v25[2];
            if ( v28 != nullptr )
            {
              RecvPkt__Rewind(this: a2);
              (*(void (__thiscall **)(void *, _DWORD *))(*(_DWORD *)v28 + 64))(a1: v28, a2);
            }
            v25 = (_DWORD *)*v25;
          }
          while ( v25 != (_DWORD *)*(this + 5413) );
        }
        RecvPkt__Rewind(this: a2);
        return CSessionStage__vf51(a1: a2);
      }
      return result;
    }
    if ( (unsigned __int16)v4 > 0x18Cu )
    {
      v20 = (unsigned __int16)v4 - 397;
      if ( v20 == 0 )
        return sub_704EF2(a1: a2);
      v21 = v20 - 1;
      if ( v21 == 0 )
        return sub_70BA8F(a1: a2);
      v22 = v21 - 1;
      if ( v22 == 0 )
        return sub_70813F(a1: a2);
      v23 = v22 - 103;
      if ( v23 == 0 )
        return sub_70BA63(a1: a2);
      if ( v23 == 1 )
        return sub_70F090(a1: a2);
      goto LABEL_138;
    }
    if ( v4 == 396 )
    {
      v19 = RecvPkt__Decode1(this: a2);
      return sub_9B5648(a1: v19);
    }
    v16 = (unsigned __int16)v4 - 358;
    if ( v16 == 0 )
      return sub_707673(a1: a2);
    v17 = v16 - 1;
    if ( v17 == 0 )
      return sub_70777C(a1: a2);
    result = v17 - 6;
    if ( result != 0 )
    {
      v18 = result - 1;
      if ( v18 == 0 )
        return sub_70058C(a1: a2);
      if ( v18 == 28 )
        sub_712567(a1: a2);
      goto LABEL_138;
    }
    if ( *(this + 5395) != 0 )
    {
      result = sub_6FA585();
      if ( result != 0 )
        return sub_6FEE31(a1: a2);
    }
  }
  return result;
}