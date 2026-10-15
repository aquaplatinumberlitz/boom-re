// CChatStage vf51 @ 0x689c63
int __thiscall CChatStage__vf51(Concurrency::details::SchedulerBase *this, _DWORD *a2)
{
  _DWORD *v2; // esi
  int v4; // eax
  int v5; // eax
  int v6; // eax
  int v7; // eax
  int v8; // eax
  int v9; // eax
  int v11; // eax
  int v12; // eax
  int v13; // eax
  int v14; // eax
  int v15; // eax
  int v16; // ebx
  unsigned __int8 v17; // al
  int v18; // eax
  int v19; // eax
  int v20; // eax
  int v21; // eax
  int v22; // eax
  char *v23; // eax
  int v24; // eax
  _DWORD *v25; // eax
  char **v26; // ecx
  int v27; // eax
  _DWORD *v28; // eax
  int *v29; // esi
  char *v30; // eax
  char *v31; // eax
  int v32; // eax
  int v33; // eax
  int v34; // eax
  int v35; // eax
  int v36; // eax
  unsigned int v37; // esi
  DWORD Time; // eax
  bool v39; // cf
  char *v40; // eax
  int v41; // eax
  char *v42; // esi
  size_t v43; // eax
  int v44; // [esp-10h] [ebp-7D7Ch] BYREF
  int v45; // [esp-Ch] [ebp-7D78h]
  int v46; // [esp-8h] [ebp-7D74h]
  int v47; // [esp-4h] [ebp-7D70h]
  int v48; // [esp+0h] [ebp-7D6Ch]
  int v49; // [esp+4h] [ebp-7D68h]
  int v50[11]; // [esp+10h] [ebp-7D5Ch] BYREF
  int *v51; // [esp+3Ch] [ebp-7D30h]
  _DWORD *v52; // [esp+40h] [ebp-7D2Ch]
  _BYTE v53[28]; // [esp+7C98h] [ebp-D4h] BYREF
  _BYTE v54[28]; // [esp+7CB4h] [ebp-B8h] BYREF
  _DWORD Src[7]; // [esp+7CD0h] [ebp-9Ch] BYREF
  _BYTE v56[28]; // [esp+7CECh] [ebp-80h] BYREF
  char v57[28]; // [esp+7D08h] [ebp-64h] BYREF
  _BYTE v58[28]; // [esp+7D24h] [ebp-48h] BYREF
  char *Str[4]; // [esp+7D40h] [ebp-2Ch] BYREF
  int v60; // [esp+7D50h] [ebp-1Ch]
  unsigned int v61; // [esp+7D54h] [ebp-18h]
  int v62; // [esp+7D68h] [ebp-4h]

  v2 = a2;
  v52 = a2;
  v4 = (unsigned __int16)RecvPkt__Decode2(this: a2);
  if ( (unsigned __int16)v4 > 0x124u )
  {
    if ( (unsigned __int16)v4 > 0x1CAu )
    {
      v32 = (unsigned __int16)v4 - 460;
      if ( v32 == 0 )
      {
        v61 = 15;
        v60 = 0;
        LOBYTE(Str[0]) = 0;
        v62 = 4;
        RecvPkt__DecodeStrInto(this: a2, a2: Str);
        goto LABEL_89;
      }
      v33 = v32 - 68;
      if ( v33 != 0 )
      {
        v34 = v33 - 21;
        if ( v34 != 0 )
        {
          v35 = v34 - 62;
          if ( v35 != 0 )
          {
            v36 = v35 - 8;
            if ( v36 != 0 )
            {
              if ( v36 == 2 )
                sub_68344F(a1: a2);
            }
            else
            {
              sub_6819FB(a1: a2);
            }
          }
          else
          {
            sub_67D9B7(a1: a2);
          }
        }
        else
        {
          sub_67CAF0(a1: a2);
        }
        goto LABEL_90;
      }
      RecvPkt__DecodeStr(this: a2, a2: Str);
      v62 = 12;
      v37 = RecvPkt__Decode4(this: a2);
      Time = timeGetTime();
      v39 = v61 < 0x10;
      *((_DWORD *)this + 3160) = v37 + Time;
      v40 = Str[0];
      if ( v39 )
        v40 = (char *)Str;
      std::string::string(Str: v40);
      LOBYTE(v62) = 13;
      v41 = sub_98DB56(a1: v54, a2: v48);
      if ( *(_DWORD *)(v41 + 20) < 0x10u )
        v42 = (char *)v41;
      else
        v42 = *(char **)v41;
      v43 = strlen(Str: v42);
      std::string::assign(Src: v42, Size: v43);
      LOBYTE(v62) = 12;
      std::string::_Tidy(a1: v54, a2: 1, Size: 0);
      *((_DWORD *)this + 3162) = 1;
    }
    else
    {
      if ( v4 != 458 )
      {
        v18 = (unsigned __int16)v4 - 293;
        if ( v18 != 0 )
        {
          v19 = v18 - 96;
          if ( v19 == 0 )
          {
            sub_689AA0(a1: a2);
            goto LABEL_90;
          }
          v20 = v19 - 4;
          if ( v20 == 0 )
          {
            sub_688D43(a1: a2);
            goto LABEL_90;
          }
          v21 = v20 - 1;
          if ( v21 == 0 )
          {
            sub_68850F(a1: a2);
            goto LABEL_90;
          }
          v22 = v21 - 62;
          if ( v22 != 0 )
          {
            if ( v22 != 1 || sub_9B6F75(a1: 2) == 0 )
              goto LABEL_90;
            sub_5F88D5(a1: this, a2: 0);
            v62 = 5;
            if ( CBuyItemListDlg__vf38(a1: 0, a2: 1, a3: 1) != 3 )
            {
              v62 = -1;
              return sub_5F85C3(a1: v48, a2: v49);
            }
            sub_5F8836(a1: Str);
            LOBYTE(v62) = 6;
            sub_88849F(a1: 329);
            LOBYTE(v62) = 7;
            v23 = (char *)sub_99A731(a1: 0);
            std::string::string(Str: v23);
            LOBYTE(v62) = 8;
            SendPkt__EncodeStr(this: v50, Src);
            LOBYTE(v62) = 7;
            std::string::_Tidy(a1: Src, a2: 1, Size: 0);
            SendPkt__EncodeStr(this: v50, Src: Str);
            sub_888609(a1: v50);
            LOBYTE(v62) = 6;
            sub_8884DC(a1: v48, a2: v49);
            LOBYTE(v62) = 5;
            std::string::_Tidy(a1: Str, a2: 1, Size: 0);
            v62 = -1;
            sub_5F85C3(a1: v48, a2: v49);
            goto LABEL_58;
          }
          v61 = 15;
          v60 = 0;
          LOBYTE(Str[0]) = 0;
          v62 = 3;
          sub_8E7B96(a1: Str);
LABEL_89:
          (*(void (__thiscall **)(Concurrency::details::SchedulerBase *, char **, _DWORD))(*(_DWORD *)this + 304))(
            a1: this,
            a2: Str,
            a3: 0);
          v62 = -1;
          std::string::_Tidy(a1: Str, a2: 1, Size: 0);
          goto LABEL_90;
        }
        if ( RecvPkt__Decode1(this: a2) != 0 )
        {
          v51 = (int *)RecvPkt__Decode4(this: a2);
          if ( (int)v51 > 0 )
          {
            sub_5DA89B(a1: v48, a2: v49);
            sub_5DA9D9(a1: v51, a2);
            CBuyItemListDlg__vf38(a1: 0, a2: 1, a3: 1);
            v62 = -1;
            return sub_5DA7B6(a1: v48, a2: v49);
          }
          std::string::string(Str: aNosearchresult);
          v62 = 1;
          v47 = 1;
          v46 = 0x10000000;
          v45 = 0x10000000;
          v27 = sub_A2A5E0(a1: 0, a2: 76, a3: 161);
          v51 = &v44;
          v28 = (_DWORD *)sub_98DB56(a1: v58, a2: v27);
          if ( v28[5] >= 0x10u )
            v28 = (_DWORD *)*v28;
          sub_5FABCC(a1: v28, a2: 0, a3: dword_EEEBD8, a4: v44, a5: v45, a6: v46, a7: v47);
          v62 = -1;
          v26 = (char **)v58;
        }
        else
        {
          std::string::string(Str: aDberrornotexis);
          v62 = 0;
          v47 = 1;
          v46 = 0x10000000;
          v45 = 0x10000000;
          v24 = sub_A2A5E0(a1: 0, a2: 76, a3: 161);
          v51 = &v44;
          v25 = (_DWORD *)sub_98DB56(a1: v53, a2: v24);
          if ( v25[5] >= 0x10u )
            v25 = (_DWORD *)*v25;
          sub_5FABCC(a1: v25, a2: 0, a3: dword_EEEBD8, a4: v44, a5: v45, a6: v46, a7: v47);
          v62 = -1;
          v26 = (char **)v53;
        }
LABEL_57:
        std::string::_Tidy(a1: v26, a2: 1, Size: 0);
LABEL_58:
        v2 = v52;
        goto LABEL_90;
      }
      v61 = 15;
      v60 = 0;
      LOBYTE(Str[0]) = 0;
      v62 = 9;
      v29 = &dword_C503B0;
      if ( sub_8E9E12(a1: dword_E60884) == 0 )
        v29 = (int *)&off_C503AC;
      std::string::string(Str: aToggleitemunli);
      LOBYTE(v62) = 10;
      v30 = (char *)sub_98DB56(a1: v56, a2: v48);
      if ( *((_DWORD *)v30 + 5) >= 0x10u )
        v30 = *(char **)v30;
      std::string::string(Str: v30);
      LOBYTE(v62) = 11;
      sub_415C67(a1: Str, Format: v57, a3: v29);
      LOBYTE(v62) = 10;
      std::string::_Tidy(a1: v57, a2: 1, Size: 0);
      LOBYTE(v62) = 9;
      std::string::_Tidy(a1: v56, a2: 1, Size: 0);
      v31 = Str[0];
      if ( v61 < 0x10 )
        v31 = (char *)Str;
      sub_67DF41(Str: v31);
    }
    v62 = -1;
    v26 = Str;
    goto LABEL_57;
  }
  if ( (unsigned __int16)v4 == 292 )
  {
    v16 = (unsigned __int8)RecvPkt__Decode1(this: a2);
    v17 = RecvPkt__Decode1(this: a2);
    sub_9B69F7(a1: v16, a2: v17);
  }
  else
  {
    if ( (unsigned __int16)v4 > 0x47u )
    {
      v11 = (unsigned __int16)v4 - 73;
      if ( v11 != 0 )
      {
        v12 = v11 - 4;
        if ( v12 != 0 )
        {
          v13 = v12 - 5;
          if ( v13 != 0 )
          {
            v14 = v13 - 46;
            if ( v14 != 0 )
            {
              v15 = v14 - 87;
              if ( v15 == 0 )
                return sub_6800B4(a1: a2);
              if ( v15 == 55 )
                return sub_6814DB(a1: a2);
            }
            else
            {
              sub_67EF33(a1: a2);
            }
          }
          else
          {
            sub_68099E(a1: a2);
          }
        }
        else
        {
          sub_67DB4A(a1: a2);
        }
      }
      else
      {
        (*(void (__thiscall **)(Concurrency::details::SchedulerBase *, _DWORD *))(*(_DWORD *)this + 536))(a1: this, a2);
      }
      goto LABEL_90;
    }
    if ( v4 == 71 )
    {
      if ( Concurrency::details::SchedulerBase::Id(this) != 0 )
      {
        sub_67F9B9(a1: a2);
        sub_6929A6(a1: 0);
      }
      else if ( dword_E61088 == 0 && dword_E62470 == 0 )
      {
        sub_67F1E3(a1: a2);
      }
      goto LABEL_90;
    }
    v5 = (unsigned __int16)v4 - 25;
    if ( v5 == 0 )
    {
      if ( sub_8DE182(a1: dword_E60928) == 0 && sub_8DE261(a1: dword_E60928) == 0 )
        sub_67DD58(a1: a2);
      goto LABEL_90;
    }
    v6 = v5 - 3;
    if ( v6 != 0 )
    {
      v7 = v6 - 1;
      if ( v7 != 0 )
      {
        v8 = v7 - 2;
        if ( v8 != 0 )
        {
          v9 = v8 - 9;
          if ( v9 == 0 )
            return sub_67E08D(a1: a2);
          if ( v9 == 7 )
            sub_67D2DA(a1: a2);
        }
        else
        {
          sub_684008(a1: a2);
        }
      }
      else
      {
        sub_67EDBD(a1: a2);
      }
      goto LABEL_90;
    }
  }
  sub_6855DF(a1: a2);
LABEL_90:
  RecvPkt__Rewind(this: v2);
  return CStage__vf51(a1: v2);
}