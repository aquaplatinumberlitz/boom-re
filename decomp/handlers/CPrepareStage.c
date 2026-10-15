// CPrepareStage vf51 @ 0x6d02d6
int __thiscall CPrepareStage__vf51(_DWORD **this, int *a2)
{
  int v3; // eax
  int v4; // eax
  int v5; // eax
  int v6; // eax
  int v7; // eax
  int v8; // eax
  int v9; // eax
  int v10; // eax
  int v11; // eax
  int v12; // eax
  int v14; // eax
  int v15; // eax
  int v16; // eax
  int v17; // eax
  int v18; // eax
  int v19; // eax
  int v20; // eax
  _BYTE v21[36]; // [esp+10h] [ebp-28h] BYREF
  int v22; // [esp+34h] [ebp-4h]

  v3 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v3 > 0x7Fu )
  {
    if ( (unsigned __int16)v3 > 0x196u )
    {
      if ( (unsigned __int16)v3 > 0x1F4u )
      {
        v19 = (unsigned __int16)v3 - 501;
        if ( v19 != 0 )
        {
          v20 = v19 - 37;
          if ( v20 != 0 )
          {
            if ( v20 == 15 )
            {
              sub_A62490(a1: v21);
              v22 = 0;
              RecvPkt__DecodeBlob(this: a2, a2: (int)v21);
              sub_6A5A5E(a1: v21);
              v22 = -1;
              sub_A62530(a1: v21);
            }
          }
          else
          {
            sub_6C98F4(a1: a2);
          }
        }
        else
        {
          sub_6C4978(a1: a2);
        }
      }
      else
      {
        if ( v3 == 500 )
          return sub_6BEAF9(a1: a2);
        v16 = (unsigned __int16)v3 - 407;
        if ( v16 == 0 )
          return sub_6C5A84(a1: a2);
        v17 = v16 - 2;
        if ( v17 != 0 )
        {
          v18 = v17 - 89;
          if ( v18 == 0 )
            return sub_6BEAE9(a1: a2);
          if ( v18 == 1 )
            return sub_6BEACC(a1: a2);
        }
        else
        {
          sub_6BDC56(a1: a2);
        }
      }
    }
    else
    {
      if ( v3 == 406 )
        return sub_6C9392(a1: a2);
      if ( (unsigned __int16)v3 > 0x121u )
      {
        v14 = (unsigned __int16)v3 - 324;
        if ( v14 == 0 )
          return sub_6BED68(a1: a2);
        v15 = v14 - 48;
        if ( v15 == 0 )
          return sub_6BDC74(a1: a2);
        if ( v15 == 25 )
          return sub_6BF69C(a1: a2);
      }
      else
      {
        if ( v3 == 289 )
          return sub_6BDC33(a1: a2);
        v10 = (unsigned __int16)v3 - 134;
        if ( v10 != 0 )
        {
          v11 = v10 - 54;
          if ( v11 != 0 )
          {
            v12 = v11 - 21;
            if ( v12 == 0 )
              return sub_6C48CD(a1: a2);
            if ( v12 == 44 )
              sub_6C2FB5(a1: a2);
          }
          else
          {
            sub_6BE9EB(a1: a2);
          }
        }
        else
        {
          sub_6C4070(a1: a2);
        }
      }
    }
  }
  else if ( (unsigned __int16)v3 == 127 )
  {
    sub_6C5767(a1: a2);
  }
  else if ( (unsigned __int16)v3 > 0x74u )
  {
    switch ( (__int16)v3 )
    {
      case 'u':
        sub_6CCE6E(a1: a2);
        break;
      case 'v':
        sub_6C0DB9(a1: a2);
        break;
      case 'w':
        sub_6BF289(a1: a2);
        break;
      case 'x':
        sub_6C8153(a1: a2);
        break;
      case 'y':
        sub_6C96A4(a1: a2);
        break;
      case 'z':
        sub_6C3F62(a1: a2);
        break;
      case '{':
        sub_6C3FE1(a1: a2);
        break;
      case '~':
        sub_6C56DE(a1: a2);
        break;
      default:
        break;
    }
  }
  else if ( v3 == 116 )
  {
    sub_6C9600(a1: a2);
  }
  else if ( (unsigned __int16)v3 > 0x6Eu )
  {
    v7 = (unsigned __int16)v3 - 111;
    if ( v7 != 0 )
    {
      v8 = v7 - 2;
      if ( v8 != 0 )
      {
        v9 = v8 - 1;
        if ( v9 != 0 )
        {
          if ( v9 == 1 )
            sub_6CF345(a1: a2);
        }
        else
        {
          sub_6C7F51(a1: a2);
        }
      }
      else
      {
        sub_6C3061(a1: a2);
      }
    }
    else
    {
      ((void (__thiscall *)(_DWORD **, int *))(*this)[151])(a1: this, a2);
    }
  }
  else if ( v3 == 110 )
  {
    ((void (__thiscall *)(_DWORD **, int *))(*this)[147])(a1: this, a2);
  }
  else
  {
    v4 = (unsigned __int16)v3 - 94;
    if ( v4 != 0 )
    {
      v5 = v4 - 12;
      if ( v5 != 0 )
      {
        v6 = v5 - 1;
        if ( v6 != 0 )
        {
          if ( v6 == 2 )
            ((void (__thiscall *)(_DWORD **, int *))(*this)[146])(a1: this, a2);
        }
        else
        {
          sub_6BE548(a1: a2);
        }
      }
      else
      {
        sub_6C6BC9(a1: a2);
      }
    }
    else
    {
      sub_6C9241(a1: a2);
    }
  }
  RecvPkt__Rewind(this: a2);
  CSessionStage__vf51(a1: a2);
  RecvPkt__Rewind(this: a2);
  return (*(int (__thiscall **)(_DWORD, int *))(**(this + 15139) + 16))(a1: *(this + 15139), a2);
}