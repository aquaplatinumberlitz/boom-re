// 0xa643f0
int __thiscall sub_A643F0(int this, int a2, size_t Size, int a4, int a5, int a6)
{
  int v6; // ecx
  unsigned __int8 v7; // dl
  unsigned __int8 v8; // bl
  unsigned __int8 v9; // al
  int v10; // edi
  int v11; // esi
  int v12; // edx
  int v13; // eax
  int v14; // eax
  size_t v15; // esi
  int v16; // ebx
  int v17; // ebx
  bool v18; // zf
  int v19; // ebx
  int v20; // esi
  int v21; // ecx
  int v22; // eax
  size_t v24; // ecx
  int v25; // esi
  unsigned __int8 v26; // al
  int v27; // [esp-14h] [ebp-28h]
  size_t v28; // [esp-10h] [ebp-24h]
  int v29; // [esp+0h] [ebp-14h]
  int v30; // [esp+4h] [ebp-10h]
  int v31; // [esp+8h] [ebp-Ch]
  char v33; // [esp+13h] [ebp-1h]
  unsigned __int8 v34; // [esp+1Ch] [ebp+8h]
  size_t Sizea; // [esp+20h] [ebp+Ch]
  int v36; // [esp+24h] [ebp+10h]

  v6 = *(_DWORD *)(this + 40);
  switch ( v6 )
  {
    case 0:
    case 1:
    case 4:
    case 5:
      v7 = 1;
      break;
    default:
      v7 = 2;
      break;
  }
  switch ( v6 )
  {
    case 1:
    case 3:
    case 5:
      v8 = 4;
      break;
    default:
      v8 = 2;
      break;
  }
  switch ( v6 )
  {
    case 4:
      v9 = 1;
      break;
    case 5:
      v9 = 4;
      break;
    default:
      v9 = 0;
      break;
  }
  v10 = v7;
  v11 = v9;
  v12 = v9 + v7 + v8;
  v30 = v9;
  v31 = v8;
  v29 = v12;
  switch ( v6 )
  {
    case 0:
    case 1:
    case 4:
    case 5:
      v33 = 1;
      break;
    default:
      v33 = 2;
      break;
  }
  v13 = *(_DWORD *)(this + 36);
  if ( v13 != 0 )
  {
    if ( (unsigned int)(v13 - 1) > 1 )
    {
      return 0;
    }
    else
    {
      v14 = v13 != 1 ? 1 : 4;
      v15 = Size - v14 - v12;
      v36 = v14;
      v16 = v8 - 1;
      v28 = v15 + v30;
      if ( v16 != 0 )
      {
        v17 = v16 - 1;
        if ( v17 != 0 )
        {
          v18 = v17 == 2;
          v19 = a2;
          if ( v18 )
            sub_A267C0(a1: v10 + a2, a2: v28);
          else
            sub_A267A0(a1: v10 + a2, a2: v28);
        }
        else
        {
          v19 = a2;
          sub_A267A0(a1: v10 + a2, a2: v28);
        }
      }
      else
      {
        v19 = a2;
        sub_A26790(a1: v10 + a2, a2: v28);
      }
      if ( v30 == 1 )
      {
        sub_A26790(a1: v19 + v31 + v10, a2: *(_BYTE *)(this + 24));
      }
      else if ( v30 == 4 )
      {
        sub_A267C0(a1: v19 + v31 + v10, a2: *(_DWORD *)(this + 24));
      }
      sub_A64240(a1: *(_DWORD *)(this + 16), a2: v19 + v29, a3: v15, a4: a6);
      v27 = *(_DWORD *)(this + 16);
      if ( v36 == 4 )
        v20 = sub_A26330(a1: a6, a2: v27, a3: v15);
      else
        v20 = (unsigned __int8)sub_A264C0(a1: a6, a2: v27, a3: v15);
      v21 = v36;
      if ( (unsigned int)(v36 + *(_DWORD *)(this + 32)) > *(_DWORD *)(this + 12) )
      {
        v22 = sub_A6C160(a1: v36 + *(_DWORD *)(this + 32));
        sub_A6C320(a1: this + 4, a2: v22);
        v21 = v36;
      }
      if ( v21 == 4 )
        sub_A26570(a1: v19 + Size - 4, a2: v20);
      else
        sub_A26540(a1: Size + v19 - v21, a2: v20);
      return 1;
    }
  }
  else
  {
    v24 = v11 + Size - v12;
    Sizea = Size - v12;
    if ( v8 == 1 )
    {
      sub_A26540(a1: v10 + a2, a2: v24);
    }
    else if ( v8 == 4 )
    {
      sub_A26570(a1: v10 + a2, a2: v24);
    }
    else
    {
      sub_A26550(a1: v10 + a2, a2: v24);
    }
    if ( v30 == 1 )
    {
      sub_A26540(a1: a2 + v8 + v10, a2: *(_BYTE *)(this + 24));
    }
    else if ( v30 == 4 )
    {
      sub_A26570(a1: a2 + v8 + v10, a2: *(_DWORD *)(this + 24));
    }
    v25 = v29 + a2;
    j__memcpy(a1: (void *)(v29 + a2), Src: *(const void **)(this + 16), Size: Sizea);
    if ( a4 != 0 )
    {
      switch ( *(_DWORD *)(this + 40) )
      {
        case 0:
        case 1:
        case 2:
        case 3:
          v34 = sub_A665B0(a1: a5, a2: *(unsigned __int8 *)(this + 28));
          if ( v33 == 1 )
          {
            sub_A26540(a1: v25, a2: v34);
            return 1;
          }
          v26 = sub_A665B0(a1: a5, a2: (unsigned __int8)BYTE1(*(_DWORD *)(this + 28)));
          sub_A26550(a1: v25, a2: (unsigned __int16)((v34 << 8) + v26));
          break;
        default:
          return 1;
      }
    }
    return 1;
  }
}