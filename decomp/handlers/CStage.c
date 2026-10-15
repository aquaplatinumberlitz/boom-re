// CStage vf51 @ 0x6a978b
int __thiscall CStage__vf51(_DWORD *this, int *a2)
{
  int result; // eax
  unsigned int v4; // ebx
  int **v5; // eax
  int *v6; // ebx
  int *v7; // eax
  int v8; // esi
  int v9; // ebx
  struct Concurrency::IExecutionContext *DefaultDestination; // eax
  int v11; // ebx
  unsigned __int8 v12; // al
  char *v13; // eax
  _BYTE *v14; // ecx
  int v15; // eax
  _DWORD *v16; // eax
  size_t v17; // esi
  int v18; // esi
  const CHAR *v19; // eax
  size_t v20; // esi
  unsigned __int8 v21; // al
  unsigned int v22; // eax
  char v23; // bl
  int v24; // eax
  char *v25; // eax
  int v26; // eax
  int v27; // [esp-10h] [ebp-F41Ch] BYREF
  int v28; // [esp-Ch] [ebp-F418h]
  int v29; // [esp-8h] [ebp-F414h] BYREF
  size_t v30; // [esp-4h] [ebp-F410h]
  int v31; // [esp+0h] [ebp-F40Ch]
  int v32; // [esp+4h] [ebp-F408h]
  _BYTE v33[4]; // [esp+10h] [ebp-F3FCh] BYREF
  int v34; // [esp+14h] [ebp-F3F8h]
  _DWORD v35[7]; // [esp+18h] [ebp-F3F4h] BYREF
  int v36; // [esp+34h] [ebp-F3D8h] BYREF
  int *v37; // [esp+38h] [ebp-F3D4h]
  int v38; // [esp+3Ch] [ebp-F3D0h] BYREF
  int v39; // [esp+40h] [ebp-F3CCh]
  int v40; // [esp+44h] [ebp-F3C8h]
  int v41; // [esp+48h] [ebp-F3C4h]
  size_t Size; // [esp+4Ch] [ebp-F3C0h] BYREF
  _BYTE v43[28]; // [esp+C228h] [ebp-31E4h] BYREF
  _BYTE v44[28]; // [esp+C244h] [ebp-31C8h] BYREF
  _BYTE v45[28]; // [esp+C260h] [ebp-31ACh] BYREF
  _BYTE v46[28]; // [esp+C27Ch] [ebp-3190h] BYREF
  _BYTE v47[28]; // [esp+C298h] [ebp-3174h] BYREF
  _BYTE v48[28]; // [esp+C2B4h] [ebp-3158h] BYREF
  int v49[4]; // [esp+C2D0h] [ebp-313Ch] BYREF
  _DWORD v50[7]; // [esp+C2E0h] [ebp-312Ch] BYREF
  _BYTE v51[10240]; // [esp+C2FCh] [ebp-3110h] BYREF
  _BYTE v52[1024]; // [esp+EAFCh] [ebp-910h] BYREF
  _BYTE Src[1024]; // [esp+EEFCh] [ebp-510h] BYREF
  CHAR v54[256]; // [esp+F2FCh] [ebp-110h] BYREF
  int v55; // [esp+F408h] [ebp-4h]

  result = (unsigned __int16)RecvPkt__Decode2(this: a2) - 2;
  switch ( result )
  {
    case 0:
      return sub_69B135(a1: a2);
    case 7:
      sub_692749(a1: a2);
      goto LABEL_7;
    case 10:
      return sub_6953BC(a1: a2);
    case 11:
      return sub_654ADE(a1: a2);
    case 12:
      sub_99514B(a1: a2);
      sub_999737(a1: dword_E60784);
      goto LABEL_7;
    case 14:
      sub_994CB0(a1: a2);
      goto LABEL_7;
    case 15:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 220))(a1: this, a2);
      goto LABEL_7;
    case 16:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 228))(a1: this, a2);
      goto LABEL_7;
    case 18:
      sub_6A3F88(a1: a2);
      goto LABEL_7;
    case 19:
      return sub_6953DE(a1: a2);
    case 20:
      v4 = RecvPkt__Decode4(this: a2);
      Size = RecvPkt__Decode4(this: a2);
      RecvPkt__Decode1(this: a2);
      sub_8F28DC(a1: v4);
      (*(void (__thiscall **)(_DWORD *, size_t, unsigned int))(*this + 224))(a1: this, a2: Size, a3: v4);
      goto LABEL_7;
    case 21:
      return (*(int (__thiscall **)(_DWORD *, int *))(*this + 236))(a1: this, a2);
    case 22:
      sub_6A6A0C(a1: a2);
      goto LABEL_7;
    case 30:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 240))(a1: this, a2);
      goto LABEL_7;
    case 33:
      return sub_6A01F2(a1: a2);
    case 39:
      return sub_65786B(a1: a2);
    case 41:
      return sub_695400(a1: a2);
    case 43:
    case 376:
    case 377:
    case 457:
    case 459:
    case 460:
    case 461:
    case 462:
      return result;
    case 49:
      return sub_696AD3(a1: a2);
    case 58:
      return sub_6992A3(a1: a2);
    case 59:
      return sub_6A6292(a1: a2);
    case 61:
      result = (unsigned __int8)RecvPkt__Decode1(this: a2);
      switch ( (unsigned __int8)result )
      {
        case 1u:
          return sub_696821(a1: a2);
        case 3u:
          return sub_6A0936(a1: a2);
        case 4u:
          return sub_6A0A24(a1: a2);
        default:
          break;
      }
      return result;
    case 62:
      return sub_6948BE(a1: a2);
    case 63:
      return sub_694A26(a1: a2);
    case 65:
      sub_679F6F(a1: a2);
      goto LABEL_7;
    case 67:
      sub_67A389(a1: a2);
      goto LABEL_7;
    case 73:
      sub_697D72(a1: a2);
      goto LABEL_7;
    case 74:
      sub_69475D(a1: a2);
      goto LABEL_7;
    case 76:
      result = sub_40176C(a1: 76);
      if ( (_BYTE)result == 0 && dword_E608B8 != 0 )
        return sub_427714(a1: a2);
      return result;
    case 78:
      result = sub_40176C(a1: 76);
      if ( (_BYTE)result != 0 )
        return result;
      v30 = (size_t)aDontloadelecdi;
      if ( Concurrency::details::UMSSchedulerProxy::GetCompletionList(this: g_pMainWnd) == (void *)13 )
      {
        std::string::string(Str: (char *)v30);
        v55 = 8;
        v13 = (char *)sub_98DB56(a1: v44, a2: v31);
        if ( *((_DWORD *)v13 + 5) >= 0x10u )
          v13 = *(char **)v13;
        std::string::string(Str: v13);
        LOBYTE(v55) = 9;
        (*(void (__thiscall **)(_DWORD *, _BYTE *, _DWORD))(*this + 304))(a1: this, a2: v43, a3: 0);
        LOBYTE(v55) = 8;
        std::string::_Tidy(a1: v43, a2: 1, Size: 0);
        v55 = -1;
        v30 = 0;
        v14 = v44;
      }
      else
      {
        std::string::string(Str: (char *)v30);
        v55 = 10;
        v30 = 1;
        v29 = 0x10000000;
        v28 = 0x10000000;
        v15 = sub_A2A5E0(a1: 0, a2: 76, a3: 161);
        v37 = &v27;
        v16 = (_DWORD *)sub_98DB56(a1: v45, a2: v15);
        if ( v16[5] >= 0x10u )
          v16 = (_DWORD *)*v16;
        sub_5FABCC(a1: v16, a2: 0, a3: dword_EEEBD8, a4: v27, a5: v28, a6: v29, a7: v30);
        v55 = -1;
        v30 = 0;
        v14 = v45;
      }
      return std::string::_Tidy(a1: v14, a2: 1, Size: v30);
    case 89:
      sub_694B5D(a1: a2);
      goto LABEL_7;
    case 98:
      return sub_6950D1(a1: a2);
    case 128:
      sub_69907A(a1: a2);
      goto LABEL_7;
    case 129:
      sub_6947A7(a1: a2);
      goto LABEL_7;
    case 130:
      sub_6947E3(a1: a2);
      goto LABEL_7;
    case 131:
      sub_694879(a1: a2);
      goto LABEL_7;
    case 208:
      return (*(int (__thiscall **)(_DWORD *, int *))(*this + 340))(a1: this, a2);
    case 209:
      sub_69467C(a1: a2);
      goto LABEL_7;
    case 211:
      return sub_69511D(a1: a2);
    case 216:
      return sub_6A8F9E(a1: a2);
    case 217:
      return sub_694993(a1: a2);
    case 218:
      result = sub_40176C(a1: 61);
      if ( (_BYTE)result == 0 )
        return sub_6949B3(a1: a2);
      return result;
    case 219:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 336))(a1: this, a2);
      goto LABEL_7;
    case 220:
      return sub_6A04BC(a1: v31, a2: v32);
    case 222:
      return sub_6949E2(a1: a2);
    case 223:
      return sub_694905(a1: a2);
    case 227:
      return sub_6A91E6(a1: a2);
    case 229:
      sub_6E0C5A(a1: a2);
      goto LABEL_7;
    case 230:
      sub_6DCAAC(a1: a2);
      goto LABEL_7;
    case 231:
      sub_6ABA33(a1: a2);
      goto LABEL_7;
    case 232:
      return sub_69B7F5(a1: a2);
    case 234:
      sub_699211(a1: a2);
      goto LABEL_7;
    case 236:
      return sub_69F0F3(a1: a2);
    case 237:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 252))(a1: this, a2);
      goto LABEL_7;
    case 248:
      return sub_90BE07(a1: a2);
    case 249:
      sub_694B46(a1: a2);
      goto LABEL_7;
    case 252:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 256))(a1: this, a2);
      goto LABEL_7;
    case 254:
      sub_695040(a1: a2);
      goto LABEL_7;
    case 256:
      sub_67A0B1(a1: a2);
      goto LABEL_7;
    case 264:
      Size = 0;
      sub_69512C(a1: a2, a2: &Size);
      if ( dword_E64030 != 0 )
        goto LABEL_89;
      if ( *(this + 120) != *(this + 121) )
      {
        v5 = (int **)unknown_libname_1382(a1: this + 120);
        v6 = *v5;
        v37 = v5[1];
        while ( v6 != v37 )
        {
          sub_4C2582(a1: v6);
          v55 = 0;
          if ( v40 != 0 )
          {
            RecvPkt__Rewind(this: a2);
            (*(void (__thiscall **)(int, int *))(*(_DWORD *)v40 + 20))(a1: v40, a2);
          }
          v55 = -1;
          if ( v41 != 0 )
            sub_401BFB();
          v6 += 2;
        }
      }
      v38 = 0;
      v39 = 0;
      v40 = 0;
      v55 = 2;
      (*(void (__thiscall **)(_DWORD *, _DWORD, int *))(*this + 464))(a1: this, a2: 0, a3: &v38);
      v55 = -1;
      sub_414B9F(a1: &v38);
      if ( (unsigned __int8)sub_40176C(a1: 178) == 0 )
      {
        v38 = 0;
        v39 = 0;
        v40 = 0;
        v55 = 3;
        (*(void (__thiscall **)(_DWORD *, _DWORD, int *))(*this + 488))(a1: this, a2: 0, a3: &v38);
        v55 = -1;
        sub_414B9F(a1: &v38);
      }
      if ( (unsigned __int8)sub_40176C(a1: 69) == 0 )
      {
        v38 = 0;
        v39 = 0;
        v40 = 0;
        v55 = 4;
        sub_692C61(a1: this);
        (*(void (__thiscall **)(_DWORD *, size_t, int *))(*this + 472))(a1: this, a2: Size, a3: &v38);
        v55 = -1;
        sub_414B9F(a1: &v38);
      }
      if ( (unsigned __int8)sub_40176C(a1: 173) == 0 )
      {
        v38 = 0;
        v39 = 0;
        v40 = 0;
        v55 = 5;
        (*(void (__thiscall **)(_DWORD *, size_t, int *))(*this + 480))(a1: this, a2: Size, a3: &v38);
        v55 = -1;
        sub_414B9F(a1: &v38);
      }
      sub_692B50(a1: this);
      sub_692B3F(a1: this);
      sub_692B61(a1: this);
      sub_692B72(a1: this);
      sub_692B83(a1: this);
      sub_692B94(a1: this);
      sub_692BA5(a1: this);
      sub_692C24(a1: this);
      goto LABEL_7;
    case 265:
      if ( dword_E64030 != 0 )
      {
LABEL_89:
        RecvPkt__Rewind(this: a2);
        return (*(int (__thiscall **)(int, int *))(*(_DWORD *)dword_E64030 + 176))(a1: dword_E64030, a2);
      }
      else
      {
        sub_69BABE(a1: a2);
        if ( *(this + 120) != *(this + 121) )
        {
          v7 = (int *)unknown_libname_1382(a1: this + 120);
          v8 = *v7;
          v9 = v7[1];
          while ( v8 != v9 )
          {
            sub_4C2582(a1: v8);
            v55 = 6;
            if ( v40 != 0 )
            {
              RecvPkt__Rewind(this: a2);
              (*(void (__thiscall **)(int, int *))(*(_DWORD *)v40 + 20))(a1: v40, a2);
            }
            v55 = -1;
            if ( v41 != 0 )
              sub_401BFB();
            v8 += 8;
          }
        }
LABEL_7:
        if ( dword_E6102C != 0 )
        {
          RecvPkt__Rewind(this: a2);
          sub_9A25C8(a1: a2);
        }
        if ( dword_E64028 != 0 )
        {
          RecvPkt__Rewind(this: a2);
          sub_601192(a1: a2);
        }
        if ( dword_E60888 != 0 )
        {
          RecvPkt__Rewind(this: a2);
          sub_92925D(a1: a2);
        }
        if ( dword_E61088 != 0 )
        {
          RecvPkt__Rewind(this: a2);
          sub_8124DE(a1: a2);
        }
        if ( dword_E62470 != 0 )
        {
          RecvPkt__Rewind(this: a2);
          sub_515518(a1: a2);
        }
        if ( dword_E6400C != 0 )
        {
          RecvPkt__Rewind(this: a2);
          sub_5F9028(a1: a2);
        }
        if ( dword_E63FCC != 0 )
        {
          RecvPkt__Rewind(this: a2);
          sub_91E9B9(a1: a2);
        }
        result = sub_40176C(a1: 80);
        if ( (_BYTE)result == 0 && dword_E64B04 != 0 )
        {
          RecvPkt__Rewind(this: a2);
          return sub_9228A1(a1: a2);
        }
      }
      return result;
    case 267:
      return sub_695821(a1: a2);
    case 269:
      return sub_90E6E3(a1: a2);
    case 270:
      return sub_90BA81(a1: a2);
    case 271:
      sub_90E9A5(a1: a2);
      return (*(int (__thiscall **)(_DWORD *))(*this + 352))(a1: this);
    case 272:
      return sub_90E8AB(a1: a2);
    case 273:
      sub_90E967(a1: a2);
      return (*(int (__thiscall **)(_DWORD *))(*this + 356))(a1: this);
    case 274:
      sub_90C500(a1: a2);
      DefaultDestination = Concurrency::details::UMSThreadVirtualProcessor::GetDefaultDestination(this: g_pMainWnd);
      return (*(int (__thiscall **)(struct Concurrency::IExecutionContext *))(*(_DWORD *)DefaultDestination + 356))(a1: DefaultDestination);
    case 275:
      return sub_694FE6(a1: a2);
    case 276:
      return sub_694FF5(a1: a2);
    case 277:
      return sub_695004(a1: a2);
    case 278:
      return sub_695013(a1: a2);
    case 279:
      return sub_695022(a1: a2);
    case 281:
      sub_694A91(a1: a2);
      goto LABEL_7;
    case 284:
      return sub_695F06(a1: a2);
    case 285:
      return sub_695F82(a1: a2);
    case 286:
      v11 = *this;
      v12 = RecvPkt__Decode1(this: a2);
      return (*(int (__thiscall **)(_DWORD *, _DWORD))(v11 + 428))(a1: this, a2: v12);
    case 289:
      v21 = RecvPkt__Decode1(this: a2);
      sub_8F2B03(a1: v21);
      v22 = RecvPkt__Decode4(this: a2);
      return sub_8B28EC(a1: v22);
    case 293:
      sub_6A1C43(a1: a2);
      goto LABEL_7;
    case 294:
      sub_6A1DBF(a1: a2);
      goto LABEL_7;
    case 295:
      return sub_6927DF(a1: a2);
    case 298:
      return sub_69ED49(a1: a2);
    case 300:
      return sub_695EE0(a1: a2);
    case 302:
      return sub_69EB99(a1: a2);
    case 303:
      return sub_69942E(a1: a2);
    case 304:
      return sub_6A8406(a1: a2);
    case 305:
      return sub_699521(a1: a2);
    case 306:
      return sub_69F70C(a1: a2);
    case 307:
      return sub_6954FF(a1: a2);
    case 308:
      return sub_6955CA(a1: a2);
    case 317:
      result = sub_40176C(a1: 39);
      if ( (_BYTE)result == 0 )
        return sub_695FE5(a1: a2);
      return result;
    case 323:
      sub_6A0C9E(a1: a2);
      goto LABEL_7;
    case 324:
      return sub_6A54E2(a1: a2);
    case 325:
      return nullsub_43(a1: a2);
    case 326:
      return nullsub_44(a1: a2);
    case 327:
      return nullsub_45(a1: a2);
    case 330:
      return sub_6983D4(a1: a2);
    case 331:
      return sub_69845F(a1: a2);
    case 334:
      return sub_69AB06(a1: a2);
    case 335:
      return sub_696BC7(a1: a2);
    case 340:
      return sub_6957A5(a1: a2);
    case 341:
      sub_6A689D(a1: &v38);
      v55 = 16;
      sub_A62490(a1: v35);
      LOBYTE(v55) = 17;
      RecvPkt__DecodeBlob(this: a2, a2: (int)v35);
      sub_A63A40(this: v35, a2: v50);
      LOBYTE(v55) = 18;
      v23 = sub_A62F40(a1: v35);
      sub_9B962B(a1: v35, a2: &v38);
      if ( v23 != 0 )
      {
        if ( v23 != 1 )
          goto LABEL_169;
        v24 = sub_6477DF(a1: &v38, a2: 0);
      }
      else
      {
        v24 = sub_6477A8(a1: &v38, a2: 0);
      }
      if ( v24 != 0 )
      {
        sub_648BBA(a1: v24, a2: 0);
        LOBYTE(v55) = 19;
        CBuyItemListDlg__vf38(a1: 1, a2: 1, a3: 1);
        LOBYTE(v55) = 18;
        sub_647953(a1: v31, a2: v32);
      }
LABEL_169:
      LOBYTE(v55) = 17;
      std::string::_Tidy(a1: v50, a2: 1, Size: 0);
      LOBYTE(v55) = 16;
      sub_A62530(a1: v35);
      v55 = -1;
      return sub_64D482(a1: v31, a2: v32);
    case 342:
      sub_A62490(a1: v35);
      v55 = 21;
      RecvPkt__DecodeBlob(this: a2, a2: (int)v35);
      sub_695800(a1: v35);
      v55 = -1;
      return sub_A62530(a1: v35);
    case 343:
      return (*(int (__thiscall **)(_DWORD *, int *))(*this + 348))(a1: this, a2);
    case 348:
      return nullsub_42(a1: a2);
    case 350:
      return sub_69F023(a1: a2);
    case 351:
      return sub_69F037(a1: a2);
    case 353:
      sub_8BE76E(a1: a2);
      result = sub_40176C(a1: 80);
      if ( (_BYTE)result == 0 && dword_E64B04 != 0 )
        return sub_91FAB3();
      return result;
    case 358:
      return sub_8BE898(a1: a2);
    case 359:
      return sub_8BE934(a1: a2);
    case 360:
      return sub_69F04B(a1: a2);
    case 361:
      return sub_69570C(a1: a2);
    case 367:
      return sub_6A448D(a1: a2);
    case 368:
      return sub_69584A(a1: a2);
    case 369:
      return sub_6929DE(a1: a2);
    case 371:
      return sub_69A79B(a1: a2);
    case 372:
      return sub_692A52(a1: a2);
    case 373:
      return sub_695A08(a1: a2);
    case 374:
      return sub_695A5A(a1: a2);
    case 375:
      return sub_8C0C95(a1: a2);
    case 378:
      sub_69494C(a1: a2);
      goto LABEL_7;
    case 379:
      if ( (unsigned __int8)sub_40176C(a1: 60) == 0 )
        sub_695AE4(a1: a2);
      goto LABEL_7;
    case 380:
      return sub_6A3007(a1: a2);
    case 381:
      return sub_6A46BD(a1: a2);
    case 382:
      return sub_6958EC(a1: a2);
    case 383:
      return sub_695933(a1: a2);
    case 384:
      return sub_69597A(a1: a2);
    case 385:
      return sub_6959C1(a1: a2);
    case 386:
      return sub_69F5C3(a1: a2);
    case 388:
      return sub_695E86(a1: a2);
    case 389:
      return sub_696B16(a1: a2);
    case 390:
      return sub_69F9E8(a1: a2);
    case 393:
      return sub_69FE06(a1: a2);
    case 402:
      return (*(int (__thiscall **)(_DWORD *, int *))(*this + 520))(a1: this, a2);
    case 403:
      return sub_695EAD(a1: a2);
    case 407:
      sub_69E45D(a1: a2);
      goto LABEL_7;
    case 419:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 344))(a1: this, a2);
      goto LABEL_7;
    case 422:
      result = sub_40176C(a1: 60);
      if ( (_BYTE)result == 0 )
        return sub_6A34D0(a1: a2);
      return result;
    case 431:
      sub_6A16FC(a1: a2);
      goto LABEL_7;
    case 437:
      sub_452C2B(a1: a2, a2: v31);
      goto LABEL_7;
    case 439:
      if ( dword_E64B00 != 0 )
        sub_837478(a1: a2);
      goto LABEL_7;
    case 444:
      sub_6A24B1(a1: a2);
      goto LABEL_7;
    case 448:
      sub_6A27BF(a1: a2);
      goto LABEL_7;
    case 450:
      sub_45317B(a1: v31, a2: v32);
      goto LABEL_7;
    case 451:
      sub_453989(a1: a2);
      goto LABEL_7;
    case 453:
      result = sub_40176C(a1: 212);
      if ( (_BYTE)result == 0 )
      {
        result = sub_8E31C0(a1: &v36);
        v55 = 11;
        if ( v36 != 0 )
        {
          Size = 0;
          memset(v52, 0, sizeof(v52));
          memset(Src, 0, sizeof(Src));
          v17 = (unsigned __int16)RecvPkt__Decode4(this: a2);
          RecvPkt__DecodeBuf(this: a2, a2: v52, Size: v17);
          v18 = sub_900AFA(a1: (int)v52, a2: v17, a3: Src, a4: (int)&Size);
          if ( v18 != 0 )
          {
            memset(v54, 0, sizeof(v54));
            std::string::string(Str: aHsDetectedEtc);
            LOBYTE(v55) = 12;
            v19 = (const CHAR *)sub_98DB56(a1: v48, a2: v31);
            if ( *((_DWORD *)v19 + 5) >= 0x10u )
              v19 = *(const CHAR **)v19;
            wsprintfA(a1: v54, a2: v19, v18);
            LOBYTE(v55) = 11;
            std::string::_Tidy(a1: v48, a2: 1, Size: 0);
            sub_900B79(lpString2: (LPCWSTR)v54);
          }
          sub_88849F(a1: 387);
          LOBYTE(v55) = 13;
          SendPkt__Encode4(this: v49, a2: v18);
          SendPkt__Encode4(this: v49, a2: Size);
          SendPkt__EncodeBuf(this: v49, Src, Size);
          sub_999838(a1: v49);
          LOBYTE(v55) = 11;
          result = sub_8884DC();
        }
        v55 = -1;
        if ( v37 != nullptr )
          return sub_401BFB();
      }
      return result;
    case 463:
      result = sub_40176C(a1: 214);
      if ( (_BYTE)result == 0 )
      {
        memset(v51, 0, sizeof(v51));
        v20 = (unsigned __int16)RecvPkt__Decode2(this: a2);
        RecvPkt__DecodeBuf(this: a2, a2: v51, Size: v20);
        sub_413427(a1: v51, a2: v20);
        return sub_412B59(a1: v29, a2: v30);
      }
      return result;
    case 495:
      sub_69E78E(a1: a2);
      goto LABEL_7;
    case 496:
      return sub_69549D(a1: a2);
    case 497:
      return sub_69548D(a1: a2);
    case 498:
      return sub_6954AD(a1: a2);
    case 504:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 232))(a1: this, a2);
      goto LABEL_7;
    case 511:
      sub_8F3D07(a1: 0);
      LOBYTE(v37) = 0;
      std::string::string(Str: aSquaremsguserm);
      v55 = 22;
      v25 = (char *)sub_98DB56(a1: v46, a2: v31);
      if ( *((_DWORD *)v25 + 5) >= 0x10u )
        v25 = *(char **)v25;
      std::string::string(Str: v25);
      LOBYTE(v55) = 23;
      v26 = sub_93E801(a1: v33, a2: v47);
      LOBYTE(v55) = 24;
      Size = (size_t)&v29;
      sub_467AFB(a1: v26, a2: v37);
      LOBYTE(v55) = 24;
      sub_940FBE(a1: v29, a2: v30);
      LOBYTE(v55) = 23;
      if ( v34 != 0 )
        sub_401BFB();
      LOBYTE(v55) = 22;
      std::string::_Tidy(a1: v47, a2: 1, Size: 0);
      v55 = -1;
      v30 = 0;
      v14 = v46;
      return std::string::_Tidy(a1: v14, a2: 1, Size: v30);
    case 512:
      if ( (unsigned __int8)sub_40176C(a1: 80) == 0 )
        sub_6927B3(a1: a2);
      goto LABEL_7;
    case 513:
      return sub_69EE23(a1: a2);
    case 514:
      return sub_69567C(a1: a2);
    case 518:
      return sub_69575A(a1: a2);
    case 522:
      sub_692763(a1: a2);
      goto LABEL_7;
    case 525:
      return sub_695783(a1: a2);
    case 531:
      return sub_6A8FDF(a1: a2);
    case 532:
      return sub_6A910A(a1: a2);
    case 533:
      if ( (unsigned __int8)sub_40176C(a1: 27) == 0 )
        sub_9C235C(a1: a2);
      goto LABEL_7;
    case 542:
      return sub_695AAC(a1: a2);
    case 544:
      return sub_69FFEE(a1: a2);
    case 554:
      return sub_6A96EB(a1: a2);
    case 556:
      return sub_696802(a1: a2);
    case 557:
      return sub_696069(a1: a2);
    case 558:
      return sub_696078(a1: a2);
    case 559:
      return sub_696087(a1: a2);
    case 560:
      return sub_696096(a1: a2);
    case 561:
      return sub_6960A5(a1: a2);
    case 562:
      return sub_6A5C21(a1: a2);
    case 563:
      return sub_6A5D2C(a1: a2);
    case 564:
      return sub_69D3BB(a1: a2);
    case 565:
      return sub_698329(a1: a2);
    case 571:
      return sub_692A28(a1: a2);
    case 572:
      return sub_6960B4(a1: a2);
    case 573:
      return sub_696102(a1: a2);
    case 574:
      return sub_69A903(a1: a2);
    case 577:
      return sub_692BBF(a1: a2);
    case 579:
      return sub_6A0B5B(a1: a2);
    case 580:
      sub_8E7F45(a1: 1);
      goto LABEL_7;
    case 583:
      sub_456BF7(a1: a2);
      goto LABEL_7;
    case 584:
      sub_456C5F(a1: a2);
      goto LABEL_7;
    case 590:
      sub_46530A(a1: a2);
      goto LABEL_7;
    case 601:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 500))(a1: this, a2);
      goto LABEL_7;
    case 603:
      (*(void (__thiscall **)(_DWORD *, int *))(*this + 496))(a1: this, a2);
      goto LABEL_7;
    case 606:
      sub_6A37BD(a1: a2);
      goto LABEL_7;
    case 607:
      sub_6A0C0E(a1: a2);
      goto LABEL_7;
    default:
      goto LABEL_7;
  }
}