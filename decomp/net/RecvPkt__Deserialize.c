// 0xa64b70
BOOL __thiscall sub_A64B70(int this, int a2, size_t Size, int a4, int a5, int a6)
{
  int v7; // ecx
  unsigned __int8 v8; // bl
  unsigned __int8 v9; // dl
  unsigned __int8 v10; // al
  int v11; // edi
  int v12; // ebx
  int v13; // eax
  int v14; // eax
  int v15; // edi
  int v17; // eax
  int v19; // eax
  int v20; // eax
  int v21; // ebx
  unsigned __int8 v22; // al
  int v23; // eax
  int v24; // [esp-8h] [ebp-28h]
  int v25; // [esp-8h] [ebp-28h]
  int v26; // [esp-4h] [ebp-24h]
  int v27; // [esp-4h] [ebp-24h]
  int v28; // [esp+Ch] [ebp-14h]
  int v29; // [esp+10h] [ebp-10h]
  int v30; // [esp+14h] [ebp-Ch]
  int v31; // [esp+18h] [ebp-8h]
  char v32; // [esp+1Fh] [ebp-1h]
  int v33; // [esp+28h] [ebp+8h]
  size_t Sizea; // [esp+2Ch] [ebp+Ch]
  int v35; // [esp+30h] [ebp+10h]

  v7 = *(_DWORD *)(this + 44);
  switch ( v7 )
  {
    case 0:
    case 1:
    case 4:
    case 5:
      v8 = 1;
      break;
    default:
      v8 = 2;
      break;
  }
  switch ( v7 )
  {
    case 1:
    case 3:
    case 5:
      v9 = 4;
      break;
    default:
      v9 = 2;
      break;
  }
  switch ( v7 )
  {
    case 4:
      v10 = 1;
      break;
    case 5:
      v10 = 4;
      break;
    default:
      v10 = 0;
      break;
  }
  v11 = v9;
  v31 = v8;
  v12 = v10 + v9 + v8;
  v29 = v10;
  v30 = v9;
  v28 = v12;
  switch ( v7 )
  {
    case 0:
    case 1:
    case 4:
    case 5:
      v32 = 1;
      break;
    default:
      v32 = 2;
      break;
  }
  v13 = *(_DWORD *)(this + 40);
  if ( v13 != 0 )
  {
    if ( (unsigned int)(v13 - 1) <= 1 )
    {
      v14 = v13 != 1 ? 1 : 4;
      v15 = Size - v14 - v12;
      v35 = v14;
      if ( v15 > 0 && sub_A6C240(a1: this + 4, a2: Size - v14 - v12) != 0 )
      {
        if ( v29 == 1 )
        {
          v17 = (unsigned __int8)sub_A26920(a1: a2 + v30 + v31);
        }
        else
        {
          if ( v29 != 4 )
          {
LABEL_23:
            if ( v35 == 4 )
              v33 = sub_A26680(a1: a2 + Size - 4);
            else
              v33 = (unsigned __int8)std::char_traits<char>::to_char_type(a1: Size + a2 - v35);
            sub_A642E0(a1: a2 + v28, a2: *(_DWORD *)(this + 16), a3: v15, a4: a6);
            if ( v32 == 1 )
            {
              *(_DWORD *)(this + 28) = (unsigned __int8)sub_A26920(a1: *(_DWORD *)(this + 16));
            }
            else if ( v32 == 2 )
            {
              *(_DWORD *)(this + 28) = (unsigned __int16)sub_A26930(a1: *(_DWORD *)(this + 16));
            }
            else
            {
              v26 = *(_DWORD *)(this + 16);
              if ( v32 == 4 )
                *(_DWORD *)(this + 28) = sub_A26950(a1: v26);
              else
                *(_DWORD *)(this + 28) = (unsigned __int16)sub_A26930(a1: v26);
            }
            *(_DWORD *)(this + 32) = v15;
            *(_DWORD *)(this + 36) = 0;
            v24 = *(_DWORD *)(this + 16);
            if ( v35 == 4 )
              return sub_A26330(a1: a6, a2: v24, a3: v15) == v33;
            else
              return (unsigned __int8)sub_A264C0(a1: a6, a2: v24, a3: v15) == v33;
          }
          v17 = sub_A26950(a1: a2 + v30 + v31);
        }
        *(_DWORD *)(this + 24) = v17;
        goto LABEL_23;
      }
    }
    return 0;
  }
  v19 = Size - v12;
  Sizea = v19;
  if ( v19 <= 0 || sub_A6C240(a1: this + 4, a2: v19) == 0 )
    return 0;
  if ( v29 == 1 )
  {
    v20 = (unsigned __int8)std::char_traits<char>::to_char_type(a1: a2 + v11 + v31);
    goto LABEL_43;
  }
  if ( v29 == 4 )
  {
    v20 = sub_A26680(a1: a2 + v11 + v31);
LABEL_43:
    *(_DWORD *)(this + 24) = v20;
  }
  j__memcpy(a1: *(void **)(this + 16), Src: (const void *)(a2 + v12), Size: Sizea);
  if ( v32 == 1 )
  {
    v21 = (unsigned __int8)std::char_traits<char>::to_char_type(a1: *(_DWORD *)(this + 16));
  }
  else if ( v32 == 2 )
  {
    v21 = (unsigned __int16)sub_A26660(a1: *(_DWORD *)(this + 16));
  }
  else
  {
    v27 = *(_DWORD *)(this + 16);
    if ( v32 == 4 )
      v21 = sub_A26680(a1: v27);
    else
      v21 = (unsigned __int16)sub_A26660(a1: v27);
  }
  if ( a4 != 0 )
  {
    switch ( *(_DWORD *)(this + 44) )
    {
      case 0:
      case 1:
      case 2:
      case 3:
        v22 = sub_A665D0(a1: a5, a2: (unsigned __int8)v21);
        if ( v32 == 1 )
        {
          v25 = *(_DWORD *)(this + 16);
          *(_DWORD *)(this + 28) = v22;
          sub_A26540(a1: v25, a2: v22);
        }
        else
        {
          v23 = (v22 << 8) + (unsigned __int8)sub_A665D0(a1: a5, a2: BYTE1(v21));
          *(_DWORD *)(this + 28) = v23;
          sub_A26550(a1: *(_DWORD *)(this + 16), a2: (unsigned __int16)v23);
        }
        break;
      default:
        goto LABEL_56;
    }
  }
  else
  {
LABEL_56:
    *(_DWORD *)(this + 28) = v21;
  }
  *(_DWORD *)(this + 32) = Sizea;
  *(_DWORD *)(this + 36) = 0;
  return 1;
}