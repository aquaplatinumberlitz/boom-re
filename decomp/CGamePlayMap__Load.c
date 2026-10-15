// CGamePlayMap::Load @ 0x7354FD (vf7)
int __userpurge CGamePlayMap__vf7@<eax>(
        __int32 a1@<ecx>,
        _DWORD *a2@<ebp>,
        void *a3,
        int a4,
        int a5,
        int a6,
        int a7,
        __int32 a8)
{
  int v8; // eax
  void *v9; // esi
  _BYTE *v12; // esi
  int v13; // eax
  char v14; // al
  int *v15; // esi
  int *v16; // esi
  char *v17; // eax
  char v18; // al
  _DWORD *v19; // esi
  char v20; // al
  _DWORD *v21; // esi
  int *v22; // esi
  int v23; // eax
  int v24; // eax
  int v25; // ecx
  int *v26; // esi
  _DWORD *v27; // eax
  int i; // edx
  int *v29; // edi
  int v30; // eax
  int v31; // eax
  bool v32; // sf
  int v33; // eax
  char *v34; // edi
  int *v35; // eax
  void *v36; // eax
  int v37; // eax
  int v38; // edi
  int v39; // eax
  int v40; // eax
  signed int v41; // edi
  void *v42; // eax
  void *v43; // eax
  void *v44; // eax
  _DWORD *v45; // eax
  int v46; // eax
  int v47; // edi
  int v48; // ecx
  _DWORD *v49; // ecx
  _DWORD *v50; // eax
  int v51; // ecx
  _DWORD *v52; // ecx
  _DWORD *v53; // eax
  int v54; // edi
  int v55; // eax
  int *v56; // ecx
  int v57; // eax
  int v58; // eax
  unsigned __int8 *v59; // eax
  int *v60; // eax
  bool v61; // cf
  int **v62; // ecx
  _DWORD *v63; // ecx
  int v64; // eax
  int v65; // eax
  int v66; // eax
  int v67; // edi
  int v68; // eax
  int v69; // eax
  int v70; // ecx
  int v71; // eax
  int v72; // eax
  int v73; // eax
  int v74; // eax
  _DWORD *v75; // eax
  int v76; // eax
  int v77; // eax
  void *v78; // eax
  int v79; // eax
  int v80; // ecx
  int v81; // eax
  unsigned __int8 *v82; // eax
  const unsigned __int8 *v83; // eax
  unsigned __int8 *v84; // eax
  char *v85; // edi
  int v86; // eax
  int v87; // eax
  int v88; // eax
  int v89; // ecx
  void *v90; // eax
  int *v91; // eax
  int **v92; // ecx
  _DWORD *v93; // ecx
  int v94; // edi
  int v95; // eax
  int v96; // eax
  int v97; // eax
  void *v98; // eax
  int v99; // eax
  _DWORD *v100; // eax
  int v101; // eax
  int v102; // eax
  int v103; // eax
  void *v104; // eax
  int *v105; // eax
  int **v106; // ecx
  _DWORD *v107; // ecx
  int v108; // edi
  int v109; // eax
  int v110; // eax
  int v111; // eax
  int *v112; // eax
  int **v113; // ecx
  _DWORD *v114; // ecx
  int v115; // edi
  int v116; // eax
  int v117; // eax
  int v118; // eax
  int *v119; // eax
  int *v120; // edi
  int v121; // eax
  int v122; // eax
  int v123; // edi
  int v124; // edi
  int v125; // edi
  int v126; // eax
  int v127; // eax
  int v128; // eax
  int v129; // eax
  int v130; // eax
  int v131; // ecx
  bool v132; // zf
  int v133; // eax
  int v134; // eax
  int v135; // edi
  int v136; // eax
  int v137; // ecx
  int v138; // eax
  unsigned __int8 *v139; // eax
  _DWORD *v140; // eax
  int v141; // eax
  int v142; // eax
  int v143; // edi
  int v144; // eax
  _DWORD *v145; // esi
  int v146; // eax
  BOOL v147; // eax
  int v148; // eax
  int v149; // eax
  int v150; // edx
  int v151; // ecx
  void *v152; // eax
  int v153; // eax
  unsigned int v154; // kr00_4
  __int32 v155; // edi
  __int32 v156; // ebx
  __int32 v157; // ecx
  __int32 v158; // ebx
  __int32 v159; // ecx
  unsigned int v160; // edx
  unsigned int v161; // edx
  __int32 v162; // edx
  __int32 v163; // esi
  __int32 *v164; // ecx
  unsigned int v165; // ebx
  __int32 v166; // edi
  __int32 v167; // eax
  __int32 v168; // edi
  int v169; // edi
  __int32 v170; // ebx
  int v171; // ecx
  __int32 v172; // ecx
  __int32 v173; // eax
  unsigned int v174; // eax
  __int32 v175; // esi
  __int32 v176; // edi
  __int32 v177; // ebx
  __int32 v178; // edi
  _DWORD v179[6]; // [esp-68h] [ebp-48Ch] BYREF
  _DWORD *v180; // [esp-50h] [ebp-474h] BYREF
  int v181; // [esp-4Ch] [ebp-470h]
  int v182; // [esp-48h] [ebp-46Ch]
  int v183; // [esp-44h] [ebp-468h]
  _DWORD *v184; // [esp-40h] [ebp-464h]
  int v185; // [esp-3Ch] [ebp-460h]
  int v186; // [esp-38h] [ebp-45Ch]
  int v187; // [esp-34h] [ebp-458h]
  int v188; // [esp-30h] [ebp-454h]
  int v189; // [esp-2Ch] [ebp-450h]
  int v190; // [esp-Ch] [ebp-430h]
  _DWORD *v191; // [esp-8h] [ebp-42Ch]
  int v192; // [esp-4h] [ebp-428h]
  int v193; // [esp+0h] [ebp-424h]
  int v194; // [esp+3A0h] [ebp-84h]
  __int32 v195; // [esp+3A4h] [ebp-80h]
  unsigned int v196; // [esp+3A8h] [ebp-7Ch]
  void ***v197; // [esp+3ACh] [ebp-78h]
  __int32 v198; // [esp+3B0h] [ebp-74h] BYREF
  void ***v199; // [esp+3B4h] [ebp-70h] BYREF
  int *v200; // [esp+3B8h] [ebp-6Ch] BYREF
  int v201; // [esp+3BCh] [ebp-68h]
  __int32 v202; // [esp+3C0h] [ebp-64h] BYREF
  _DWORD v203[18]; // [esp+3C4h] [ebp-60h] BYREF
  __int32 v204; // [esp+40Ch] [ebp-18h] BYREF
  __int32 v205; // [esp+410h] [ebp-14h] BYREF
  __int32 v206; // [esp+414h] [ebp-10h] BYREF
  void ***v207; // [esp+418h] [ebp-Ch] BYREF
  __int32 *v208; // [esp+41Ch] [ebp-8h] BYREF
  __int32 v209; // [esp+420h] [ebp-4h] BYREF
  unsigned int savedregs; // [esp+424h] [ebp+0h] BYREF
  void ***retaddr; // [esp+428h] [ebp+4h] BYREF

  v8 = a2[4];
  v9 = (void *)a2[2];
  *(a2 - 202) = v9;
  *(a2 - 219) = v8;
  *(_BYTE *)(a1 + 11023112) = 1;
  sub_5CA14D(a1: a2 - 218);
  sub_731EEC(a1: a2 - 205, a2: *(_DWORD *)(a1 + 127476), a3: *(_DWORD *)(a1 + 127480));
  sub_A37080();
  *(a2 - 1) = 0;
  if ( CDataI16Alpha__vf4(this: a2 - 97, Src: v9) == 0 )
    goto LABEL_2;
  v12 = (_BYTE *)sub_A34DF0(a1: a2 - 97);
  v13 = sub_A34DE0(a1: a2 - 97);
  v14 = Crc32Update(a1: 0, a2: v12, a3: v13);
  sub_44AD23(a1: v14);
  v192 = *(_DWORD *)v12;
  v15 = (int *)(v12 + 4);
  sub_413F32(a1: v192);
  if ( sub_414543(a1: (char *)dword_8F4818 + a1) < 1000 )
  {
    v18 = sub_414543(a1: (char *)dword_8F4818 + a1);
    sub_413F32(a1: v18);
    sub_413F32(a1: 232);
    sub_413F32(a1: 12);
    v192 = 1;
  }
  else
  {
    v192 = *v15;
    v16 = v15 + 1;
    sub_413F32(a1: v192);
    v192 = *v16++;
    sub_413F32(a1: v192);
    v17 = (char *)*v16;
    v15 = v16 + 1;
    v192 = (int)v17;
  }
  sub_413F32(a1: v192);
  v192 = *v15;
  v19 = v15 + 1;
  sub_413F32(a1: v192);
  sub_413F32(a1: *v19);
  sub_44AD23(a1: v19[5]);
  v20 = sub_44B21E(a1: (char *)dword_8F47C8 + a1);
  sub_44AD23(a1: -24 * v20);
  *(_DWORD *)((char *)&loc_8F47C2 + a1 + 2) = sub_8E77F4(a1: dword_E60884);
  v19 += 8;
  *(_DWORD *)((char *)&loc_A513EF + a1 + 1) = *v19++;
  *(_DWORD *)((char *)nullsub_3641 + a1) = *v19++;
  *(_DWORD *)((char *)&loc_A513F7 + a1 + 1) = *v19++;
  *(_DWORD *)((char *)sub_A513FC + a1) = *v19;
  v21 = v19 + 1;
  if ( sub_8E78DB(a1: dword_E60884) != 16 && sub_8E78DB(a1: dword_E60884) != 32 )
    goto LABEL_10;
  if ( *(_DWORD *)((char *)&loc_A513EF + a1 + 1) != 0 )
  {
LABEL_2:
    *(a2 - 1) = -1;
    sub_A35800(a1: a2 - 97);
  }
  else
  {
LABEL_10:
    v22 = v21 + 2;
    sub_4127AD(a1: a2 - 205, a2: *(int *)((char *)&dword_8F4848 + a1), a3: *(int *)((char *)&dword_8F484C + a1));
    v23 = sub_414543(a1: (char *)dword_8F483C + a1);
    sub_4129AA(a1: v23);
    for ( *(a2 - 194) = 0; *(a2 - 194) < sub_414543(a1: (char *)dword_8F483C + a1); ++*(a2 - 194) )
    {
      v24 = *(a2 - 194);
      *(_DWORD *)(*(int *)((char *)&dword_8F4848 + a1) + 8 * v24) = *v22;
      *(_DWORD *)(*(int *)((char *)&dword_8F4848 + a1) + 8 * v24 + 4) = v22[1];
      v22 += 2;
    }
    v25 = *v22;
    *(a2 - 205) = *v22;
    v26 = v22 + 1;
    v27 = a2 - 44;
    for ( i = 19; i >= 0; --i )
    {
      *v27 = 0;
      v27[1] = 0;
      v27 += 2;
    }
    if ( v25 > 0 )
    {
      v29 = a2 - 44;
      *(a2 - 201) = v25;
      do
      {
        v30 = *v26;
        *v29 = *v26;
        if ( v30 >= 0 )
          sub_414543(a1: (char *)dword_8F4800 + a1);
        v31 = v26[1];
        v29[1] = v31;
        if ( v31 >= 0 )
          sub_414543(a1: (char *)dword_8F480C + a1);
        v32 = *v29 < 0;
        v29[2] = v26[2];
        if ( !v32 )
          sub_414543(a1: (char *)dword_8F4800 + a1);
        v33 = v26[3];
        v26 += 4;
        v32 = v29[1] < 0;
        v29[3] = v33;
        if ( !v32 )
          sub_414543(a1: (char *)dword_8F480C + a1);
        v29 += 4;
        v132 = (*(a2 - 201))-- == 1;
      }
      while ( !v132 );
    }
    *(a2 - 197) = 0;
    if ( sub_414543(a1: (char *)dword_8F4818 + a1) == 1000 || sub_414543(a1: (char *)dword_8F4818 + a1) < 1001 )
    {
      v34 = (char *)dword_8F480C + a1;
      *(a2 - 195) = sub_414543(a1: (char *)dword_8F480C + a1);
      v35 = &v26[2 * *(a2 - 195) * sub_414543(a1: (char *)dword_8F4800 + a1)];
    }
    else
    {
      v34 = (char *)dword_8F480C + a1;
      *(a2 - 195) = sub_414543(a1: (char *)dword_8F480C + a1);
      v35 = &v26[3 * *(a2 - 195) * sub_414543(a1: (char *)dword_8F4800 + a1)];
    }
    v192 = *(a2 - 202);
    *(a2 - 197) = v35;
    std::string::string(Str: (char *)v192);
    *((_BYTE *)a2 - 4) = 1;
    v36 = (void *)sub_415008(a1: a2 - 65, a2: 4, a3: -1);
    *((_BYTE *)a2 - 4) = 2;
    sub_40E909(a1: a2 - 79, Src: v36);
    *((_BYTE *)a2 - 4) = 1;
    std::string::_Tidy(a1: a2 - 65, a2: 1, Size: 0);
    *(a2 - 195) = sub_6E2075(a1: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2));
    v37 = sub_414543(a1: v34);
    v192 = a2[3];
    v38 = v37;
    v39 = sub_414543(a1: (char *)dword_8F4800 + a1);
    sub_89D56E(a1: a2 - 197, a2: v38 * v39, a3: a2 - 79, a4: v192);
    v40 = *(_DWORD *)a1;
    v192 = (int)(a2 - 197);
    (*(void (__thiscall **)(__int32))(v40 + 100))(a1);
    v41 = *(_DWORD *)*(a2 - 197);
    *(a2 - 197) += 4;
    v42 = operator new[](a1: v41 + 1);
    *(a2 - 201) = v42;
    *(a2 - 243) = v42;
    *((_BYTE *)a2 - 4) = 3;
    memset(a1: v42, Val: 0, Size: v41 + 1);
    memcpy(a1: (void *)*(a2 - 201), Src: (const void *)*(a2 - 197), Size: v41);
    *(a2 - 197) += v41;
    *(a2 - 68) = 0;
    *(a2 - 67) = 15;
    *((_BYTE *)a2 - 288) = 0;
    *((_BYTE *)a2 - 4) = 4;
    sub_AA8BA3(a1: v192, a2: v193);
    *((_BYTE *)a2 - 4) = 5;
    *(a2 - 199) = 0;
    if ( v41 > 0 )
    {
      std::string::string(Str: (char *)*(a2 - 201));
      *((_BYTE *)a2 - 4) = 6;
      v43 = (void *)sub_A234E0(a1: a2 - 51, a2: a2 - 65);
      *((_BYTE *)a2 - 4) = 7;
      v44 = (void *)sub_991791(a1: a2 - 58, a2: v43);
      *((_BYTE *)a2 - 4) = 8;
      sub_40E909(a1: a2 - 72, Src: v44);
      *((_BYTE *)a2 - 4) = 7;
      std::string::_Tidy(a1: a2 - 58, a2: 1, Size: 0);
      *((_BYTE *)a2 - 4) = 6;
      std::string::_Tidy(a1: a2 - 51, a2: 1, Size: 0);
      *((_BYTE *)a2 - 4) = 5;
      std::string::_Tidy(a1: a2 - 65, a2: 1, Size: 0);
      v45 = (_DWORD *)*(a2 - 72);
      if ( *(a2 - 67) < 0x10u )
        v45 = a2 - 72;
      TiXmlDocument__vf2(a1: v45, a2: 0, a3: 0);
      if ( *((_BYTE *)a2 - 1000) == 0 )
      {
        v46 = sub_AA7EAE(Str2: aMapscript);
        v47 = v46;
        *(a2 - 199) = v46;
        if ( v46 != 0 )
        {
          sub_73022F(a1: *(a2 - 202), a2: v46);
          sub_7353AF(a1: *(a2 - 202), a2: v47);
          sub_73395A(a1: *(a2 - 202), a2: v47);
        }
      }
    }
    if ( *(int *)((char *)&dword_A832A8 + a1) != 0 )
    {
      v48 = *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2);
      if ( v48 != 0 && sub_6E2075(a1: v48) != 0 )
      {
        sub_733899(a1: v192, a2: v193);
        *((_BYTE *)a2 - 4) = 9;
        sub_9773FB(a1: a2 - 223);
        v49 = (_DWORD *)*(a2 - 222);
        v50 = (_DWORD *)*v49;
        *(a2 - 193) = *v49;
        if ( v50 != v49 )
        {
          do
          {
            v191 = v50 + 4;
            v190 = v50[3];
            sub_6E2075(a1: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2));
            sub_89DADD(a1: v190, a2: v191);
            sub_72295E(a1: a2 - 193);
            v50 = (_DWORD *)*(a2 - 193);
          }
          while ( v50 != (_DWORD *)*(a2 - 222) );
        }
        *((_BYTE *)a2 - 4) = 5;
        sub_7337B8(a1: v192, a2: v193);
      }
    }
    if ( *(_DWORD *)(a1 + 11023024) != 0 )
    {
      v51 = *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2);
      if ( v51 != 0 && sub_6E2075(a1: v51) != 0 )
      {
        sub_733899(a1: v192, a2: v193);
        *((_BYTE *)a2 - 4) = 11;
        sub_976369(a1: a2 - 223);
        v52 = (_DWORD *)*(a2 - 222);
        v53 = (_DWORD *)*v52;
        *(a2 - 193) = *v52;
        if ( v53 != v52 )
        {
          do
          {
            v191 = v53 + 4;
            v190 = v53[3];
            sub_6E2075(a1: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2));
            sub_89DADD(a1: v190, a2: v191);
            sub_72295E(a1: a2 - 193);
            v53 = (_DWORD *)*(a2 - 193);
          }
          while ( v53 != (_DWORD *)*(a2 - 222) );
        }
        *((_BYTE *)a2 - 4) = 5;
        sub_7337B8(a1: v192, a2: v193);
      }
    }
    (*(void (__thiscall **)(__int32))(*(_DWORD *)a1 + 16))(a1);
    *(a2 - 194) = 0;
    if ( sub_414543(a1: (char *)dword_8F480C + a1) > 0 )
    {
      while ( 1 )
      {
        *(a2 - 196) = 0;
        if ( sub_414543(a1: (char *)dword_8F4800 + a1) > 0 )
          break;
LABEL_190:
        ++*(a2 - 194);
        if ( *(a2 - 194) >= sub_414543(a1: (char *)dword_8F480C + a1) )
          goto LABEL_191;
      }
      *(a2 - 200) = 101 * *(a2 - 194);
      *(a2 - 234) = 40 * *(a2 - 194) + 39;
      while ( 1 )
      {
        v54 = *(a2 - 196);
        v55 = *(a2 - 200);
        v191 = (_DWORD *)*(a2 - 234);
        v56 = (int *)(584 * (v54 + v55) + a1 + 127496);
        v57 = *v56;
        v190 = 40 * v54;
        (*(void (__thiscall **)(int *))(v57 + 104))(a1: v56);
        v58 = *v26;
        if ( *v26 == -1 )
        {
          v78 = j__malloc(Size: 0xECu);
          *(a2 - 198) = v78;
          *((_BYTE *)a2 - 4) = 14;
          v79 = v78 != nullptr ? sub_5C0095(a1: v190, a2: v191) : 0;
          *((_BYTE *)a2 - 4) = 5;
          v80 = v54 + *(a2 - 200) + 1265;
          v67 = *(a2 - 196);
          *(_DWORD *)(a1 + 4 * v80) = v79;
        }
        else
        {
          *(a2 - 54) = 0;
          *(a2 - 53) = 15;
          *((_BYTE *)a2 - 232) = 0;
          *((_BYTE *)a2 - 4) = 13;
          sub_5C5965(a1: v58, a2: a2 - 58);
          v59 = (unsigned __int8 *)*(a2 - 58);
          if ( *(a2 - 53) < 0x10u )
            v59 = (unsigned __int8 *)(a2 - 58);
          sub_97798C(Str2: v59, a2: (int)(a2 - 218));
          v60 = (int *)sub_72E942(a1: a2 - 218, a2: v190);
          v61 = *(a2 - 53) < 0x10u;
          v62 = (int **)(a1 + 4 * (v54 + *(a2 - 200) + 1265));
          *(a2 - 198) = v62;
          *v62 = v60;
          v63 = (_DWORD *)*(a2 - 58);
          *(a2 - 195) = v60;
          if ( v61 )
            v63 = a2 - 58;
          v64 = *v60;
          *(a2 - 193) = v63;
          *(a2 - 192) = v64;
          v65 = sub_4C37CF(a1: a2 - 218);
          v66 = sub_4C37F1(a1: a2 - 218, a2: v65);
          v67 = *(a2 - 196);
          (*(void (__thiscall **)(_DWORD, _DWORD, _DWORD, _DWORD, int, int))(*(a2 - 192) + 132))(
            a1: *(a2 - 195),
            a2: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2),
            a3: *(a2 - 193),
            a4: *(a2 - 194),
            a5: v67,
            a6: v66);
          v68 = sub_58D8C4(a1: 0);
          *(a2 - 193) = v68;
          if ( v68 != 0 )
          {
            v69 = (*(int (__thiscall **)(int, _DWORD))(*(_DWORD *)v68 + 36))(a1: v68, a2: 0);
            v70 = *(a2 - 193);
            *(a2 - 198) = v69;
            *(a2 - 195) = (*(int (__thiscall **)(int, _DWORD))(*(_DWORD *)v70 + 40))(a1: v70, a2: 0);
            sub_72013D(a1: *(a2 - 198) / 40 + 1);
            sub_720153(a1: *(a2 - 195) / 40 + 1);
          }
          if ( sub_5CA167(a1: a2 - 218) != 0 )
          {
            v71 = *(a2 - 194) - sub_4C37F1(a1: a2 - 218, a2: v189) + 1;
            *(a2 - 193) = v71;
            if ( v71 <= *(a2 - 194) )
            {
              v72 = sub_4C37CF(a1: a2 - 218) + v67 - 1;
              do
              {
                for ( *(a2 - 192) = v67; *(a2 - 192) <= v72; v72 = sub_4C37CF(a1: a2 - 218) + v67 - 1 )
                {
                  sub_7295D8(a1: *(a2 - 193), a2: *(a2 - 192), a3: 1);
                  ++*(a2 - 192);
                }
                ++*(a2 - 193);
              }
              while ( *(a2 - 193) <= *(a2 - 194) );
            }
          }
          if ( sub_5CA183(a1: a2 - 218) != 0 )
          {
            v73 = *(a2 - 194) - sub_4C37F1(a1: a2 - 218, a2: v189) + 1;
            *(a2 - 192) = v73;
            if ( v73 <= *(a2 - 194) )
            {
              v74 = sub_4C37CF(a1: a2 - 218) + v67 - 1;
              do
              {
                for ( *(a2 - 193) = v67; *(a2 - 193) <= v74; v74 = sub_4C37CF(a1: a2 - 218) + v67 - 1 )
                {
                  sub_7298E9(a1: *(a2 - 192), a2: *(a2 - 193));
                  ++*(a2 - 193);
                }
                ++*(a2 - 192);
              }
              while ( *(a2 - 192) <= *(a2 - 194) );
            }
          }
          if ( sub_58D4DA(a1: (char *)&off_8F4858 + a1) == 0
            && *(a2 - 213) == -1
            && sub_4C37CF(a1: a2 - 218) == 1
            && sub_4C37F1(a1: a2 - 218, a2: v189) == 1 )
          {
            v75 = (_DWORD *)*(a2 - 58);
            if ( *(a2 - 53) < 0x10u )
              v75 = a2 - 58;
            v188 = 1;
            v187 = 1;
            v186 = 0;
            v185 = 0;
            v184 = v75;
            v183 = *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2);
            (*(void (__thiscall ***)(char *))((char *)&off_8F4858 + a1))[33](a1: (char *)&off_8F4858 + a1);
          }
          if ( sub_71F913(a1: a2 - 218) != 0 )
          {
            v76 = *(a2 - 194) - sub_4C37F1(a1: a2 - 218, a2: v183) + 1;
            *(a2 - 192) = v76;
            if ( v76 <= *(a2 - 194) )
            {
              v77 = sub_4C37CF(a1: a2 - 218) + v67 - 1;
              do
              {
                for ( *(a2 - 193) = v67; *(a2 - 193) <= v77; v77 = sub_4C37CF(a1: a2 - 218) + v67 - 1 )
                {
                  sub_72975F(a1: *(a2 - 192), a2: *(a2 - 193), a3: 1);
                  ++*(a2 - 193);
                }
                ++*(a2 - 192);
              }
              while ( *(a2 - 192) <= *(a2 - 194) );
            }
          }
          *((_BYTE *)a2 - 4) = 5;
          std::string::_Tidy(a1: a2 - 58, a2: 1, Size: 0);
        }
        v81 = v26[1];
        v26 += 2;
        if ( v81 != -1 )
          break;
LABEL_181:
        if ( sub_414543(a1: (char *)dword_8F4818 + a1) != 1000 && sub_414543(a1: (char *)dword_8F4818 + a1) >= 1001 )
        {
          v138 = *v26++;
          if ( v138 != -1 )
          {
            *(a2 - 61) = 0;
            *(a2 - 60) = 15;
            *((_BYTE *)a2 - 260) = 0;
            *((_BYTE *)a2 - 4) = 33;
            sub_5C5965(a1: v138, a2: a2 - 65);
            v139 = (unsigned __int8 *)*(a2 - 65);
            if ( *(a2 - 60) < 0x10u )
              v139 = (unsigned __int8 *)(a2 - 65);
            sub_97798C(Str2: v139, a2: (int)(a2 - 218));
            v140 = (_DWORD *)*(a2 - 65);
            if ( *(a2 - 60) < 0x10u )
              v140 = a2 - 65;
            *(a2 - 195) = v140;
            v180 = (_DWORD *)sub_4C37F1(a1: a2 - 218, a2: v181);
            v141 = sub_4C37CF(a1: a2 - 218);
            v142 = sub_5BEF8F(Str: (char *)*(a2 - 195), a2: v67, a3: *(a2 - 194), a4: v141, a5: (int)v180);
            *((_BYTE *)a2 - 4) = 34;
            sub_733750(a1: v142);
            *((_BYTE *)a2 - 4) = 33;
            sub_5BF014(a1: v181, a2: v182);
            *((_BYTE *)a2 - 4) = 5;
            std::string::_Tidy(a1: a2 - 65, a2: 1, Size: 0);
          }
        }
        v143 = v67 + 1;
        *(a2 - 196) = v143;
        if ( v143 >= sub_414543(a1: (char *)dword_8F4800 + a1) )
          goto LABEL_190;
      }
      *(a2 - 47) = 0;
      *(a2 - 46) = 15;
      *((_BYTE *)a2 - 204) = 0;
      *((_BYTE *)a2 - 4) = 15;
      sub_5C5965(a1: v81, a2: a2 - 51);
      v82 = (unsigned __int8 *)*(a2 - 51);
      if ( *(a2 - 46) < 0x10u )
        v82 = (unsigned __int8 *)(a2 - 51);
      sub_97798C(Str2: v82, a2: (int)(a2 - 218));
      v83 = (const unsigned __int8 *)*(a2 - 51);
      if ( *(a2 - 46) < 0x10u )
        v83 = (const unsigned __int8 *)(a2 - 51);
      if ( _mbsstr(Str: v83, Substr: aTile33) != nullptr )
      {
        v84 = (unsigned __int8 *)*(a2 - 51);
        if ( *(a2 - 46) < 0x10u )
          v84 = (unsigned __int8 *)(a2 - 51);
        sub_723F4A(a1: *(a2 - 194), a2: v67, Str1: v84);
      }
      *(a2 - 204) = 0;
      *(a2 - 203) = 0;
      *((_BYTE *)a2 - 4) = 17;
      switch ( *(a2 - 218) )
      {
        case 1:
          v112 = (int *)sub_72E66B(a1: v183, a2: v184);
          v61 = *(a2 - 46) < 0x10u;
          v113 = (int **)(a1 + 4 * (*(a2 - 200) + v67) + 45864);
          *(a2 - 192) = v113;
          *v113 = v112;
          v114 = (_DWORD *)*(a2 - 51);
          *(a2 - 198) = v112;
          if ( v61 )
            v114 = a2 - 51;
          v115 = *v112;
          *(a2 - 195) = v114;
          v116 = sub_4C37CF(a1: a2 - 218);
          v117 = sub_4C37F1(a1: a2 - 218, a2: v116);
          (*(void (__thiscall **)(_DWORD, _DWORD, _DWORD, _DWORD, _DWORD, int))(v115 + 132))(
            a1: *(a2 - 198),
            a2: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2),
            a3: *(a2 - 195),
            a4: *(a2 - 194),
            a5: *(a2 - 196),
            a6: v117);
          v118 = sub_58D719(a1: a2 - 221);
          *((_BYTE *)a2 - 4) = 24;
          sub_5AA0F2(a1: v118);
          *((_BYTE *)a2 - 4) = 17;
          v89 = *(a2 - 220);
          break;
        case 2:
          if ( *(a2 - 216) != 0 )
          {
            v98 = j__malloc(Size: 0xECu);
            *(a2 - 198) = v98;
            *((_BYTE *)a2 - 4) = 18;
            if ( v98 != nullptr )
              v99 = ((int (__thiscall *)(void *, int))loc_5C07F0)(a1: v98, a2: v183);
            else
              v99 = 0;
            *((_BYTE *)a2 - 4) = 17;
            *(_DWORD *)(a1 + 4 * *(_DWORD *)(a1 + 127472) + 86668) = v99;
            v100 = (_DWORD *)*(a2 - 51);
            if ( *(a2 - 46) < 0x10u )
              v100 = a2 - 51;
            v183 = *(_DWORD *)(a1 + 127472);
            *(a2 - 195) = v100;
            v101 = sub_4C37CF(a1: a2 - 218);
            v102 = sub_4C37F1(a1: a2 - 218, a2: v101);
            sub_5C0894(
              a1: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2),
              Str: (unsigned __int8 *)*(a2 - 195),
              a3: *(a2 - 194),
              a4: *(a2 - 196),
              a5: v102,
              a6: v182,
              a7: v183);
            v103 = sub_58D719(a1: a2 - 240);
            *((_BYTE *)a2 - 4) = 19;
            sub_5AA0F2(a1: v103);
            *((_BYTE *)a2 - 4) = 17;
            if ( *(a2 - 239) != 0 )
              ((void (*)(void))sub_401BFB)();
            ++*(_DWORD *)(a1 + 127472);
            goto LABEL_129;
          }
          v104 = j__malloc(Size: 0xF4u);
          *(a2 - 198) = v104;
          *((_BYTE *)a2 - 4) = 21;
          if ( v104 != nullptr )
            v105 = (int *)sub_5BF25F(a1: v183, a2: v184);
          else
            v105 = nullptr;
          *(a2 - 193) = v105;
          *((_BYTE *)a2 - 4) = 17;
          v61 = *(a2 - 46) < 0x10u;
          v106 = (int **)(a1 + 4 * (*(a2 - 200) + v67) + 45864);
          *(a2 - 192) = v106;
          *v106 = v105;
          v107 = (_DWORD *)*(a2 - 51);
          if ( v61 )
            v107 = a2 - 51;
          v108 = *v105;
          *(a2 - 195) = v107;
          v109 = sub_4C37CF(a1: a2 - 218);
          v110 = sub_4C37F1(a1: a2 - 218, a2: v109);
          (*(void (__thiscall **)(_DWORD, _DWORD, _DWORD, _DWORD, _DWORD, int))(v108 + 132))(
            a1: *(a2 - 193),
            a2: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2),
            a3: *(a2 - 195),
            a4: *(a2 - 194),
            a5: *(a2 - 196),
            a6: v110);
          v111 = sub_58D719(a1: a2 - 238);
          *((_BYTE *)a2 - 4) = 22;
          sub_5AA0F2(a1: v111);
          *((_BYTE *)a2 - 4) = 17;
          v89 = *(a2 - 237);
          break;
        case 3:
          v90 = j__malloc(Size: 0xE0u);
          *(a2 - 198) = v90;
          *((_BYTE *)a2 - 4) = 26;
          if ( v90 != nullptr )
            v91 = (int *)sub_5C12BF(a1: v183, a2: v184);
          else
            v91 = nullptr;
          *(a2 - 195) = v91;
          *((_BYTE *)a2 - 4) = 17;
          v61 = *(a2 - 46) < 0x10u;
          v92 = (int **)(a1 + 4 * (*(a2 - 200) + v67) + 45864);
          *(a2 - 192) = v92;
          *v92 = v91;
          v93 = (_DWORD *)*(a2 - 51);
          if ( v61 )
            v93 = a2 - 51;
          v94 = *v91;
          *(a2 - 193) = v93;
          v95 = sub_4C37CF(a1: a2 - 218);
          v96 = sub_4C37F1(a1: a2 - 218, a2: v95);
          (*(void (__thiscall **)(_DWORD, _DWORD, _DWORD, _DWORD, _DWORD, int))(v94 + 132))(
            a1: *(a2 - 195),
            a2: *(_DWORD *)((char *)&loc_8F47B2 + a1 + 2),
            a3: *(a2 - 193),
            a4: *(a2 - 194),
            a5: *(a2 - 196),
            a6: v96);
          v97 = sub_58D719(a1: a2 - 236);
          *((_BYTE *)a2 - 4) = 27;
          sub_5AA0F2(a1: v97);
          *((_BYTE *)a2 - 4) = 17;
          v89 = *(a2 - 235);
          break;
        case 4:
          v85 = (char *)*(a2 - 51);
          if ( *(a2 - 46) < 0x10u )
            v85 = (char *)(a2 - 51);
          v182 = sub_4C37F1(a1: a2 - 218, a2: v183);
          v86 = sub_4C37CF(a1: a2 - 218);
          v87 = sub_5BEF8F(Str: v85, a2: *(a2 - 196), a3: *(a2 - 194), a4: v86, a5: v182);
          *((_BYTE *)a2 - 4) = 29;
          sub_733750(a1: v87);
          *((_BYTE *)a2 - 4) = 17;
          sub_5BF014(a1: v183, a2: v184);
          v88 = sub_58D719(a1: a2 - 242);
          *((_BYTE *)a2 - 4) = 30;
          sub_5AA0F2(a1: v88);
          *((_BYTE *)a2 - 4) = 17;
          v89 = *(a2 - 241);
          break;
        default:
LABEL_132:
          if ( sub_5CA167(a1: a2 - 218) != 0 )
          {
            v124 = *(a2 - 194) - sub_4C37F1(a1: a2 - 218, a2: v181);
            while ( ++v124 <= *(a2 - 194) )
            {
              for ( *(a2 - 192) = *(a2 - 196); *(a2 - 192) <= *(a2 - 196) - 1 + sub_4C37CF(a1: a2 - 218); ++*(a2 - 192) )
              {
                sub_7294CA(a1: v124, a2: *(a2 - 192));
                sub_72991D(a1: v124, a2: *(a2 - 192), a3: 1);
                if ( *(a2 - 218) == 1 )
                  sub_729616(a1: v124, a2: *(a2 - 192), a3: 1);
              }
            }
          }
          v125 = *(a2 - 196);
          if ( sub_5CA183(a1: a2 - 218) != 0 )
          {
            v126 = *(a2 - 194) - sub_4C37F1(a1: a2 - 218, a2: v181) + 1;
            *(a2 - 192) = v126;
            if ( v126 <= *(a2 - 194) )
            {
              v127 = sub_4C37CF(a1: a2 - 218) + v125 - 1;
              do
              {
                for ( *(a2 - 193) = v125; *(a2 - 193) <= v127; v127 = sub_4C37CF(a1: a2 - 218) + v125 - 1 )
                {
                  sub_7298E9(a1: *(a2 - 192), a2: *(a2 - 193));
                  ++*(a2 - 193);
                }
                ++*(a2 - 192);
              }
              while ( *(a2 - 192) <= *(a2 - 194) );
            }
          }
          *(a2 - 192) = -1;
          while ( 1 )
          {
            v128 = *(a2 - 218);
            if ( v128 == 0 )
            {
              v133 = 0;
              goto LABEL_171;
            }
            v129 = v128 - 1;
            if ( v129 != 0 )
            {
              if ( v129 == 1 )
              {
                v130 = *(a2 - 192);
                switch ( v130 )
                {
                  case -1:
                    v131 = 0;
                    v132 = (*(_BYTE *)(a2 - 215) & 0x10) == 16;
                    goto LABEL_159;
                  case 0:
                    v131 = 0;
                    v132 = (*(_BYTE *)(a2 - 215) & 4) == 4;
                    goto LABEL_159;
                  case 1:
                    v131 = 0;
                    v132 = (*(_BYTE *)(a2 - 215) & 8) == 8;
                    goto LABEL_159;
                  case 2:
                    v131 = 0;
                    v132 = (*(_BYTE *)(a2 - 215) & 1) == 1;
                    goto LABEL_159;
                  case 3:
                    v131 = 0;
                    v132 = (*(_BYTE *)(a2 - 215) & 2) == 2;
LABEL_159:
                    LOBYTE(v131) = v132;
                    v133 = v131;
LABEL_171:
                    if ( v133 != 0 )
                    {
                      v135 = *(a2 - 194) - sub_4C37F1(a1: a2 - 218, a2: v181) + 1;
                      if ( v135 <= *(a2 - 194) )
                      {
                        v136 = sub_4C37CF(a1: a2 - 218) + *(a2 - 196) - 1;
                        do
                        {
                          v137 = *(a2 - 196);
                          for ( *(a2 - 193) = v137; *(a2 - 193) <= v136; v136 = sub_4C37CF(a1: a2 - 218)
                                                                              + *(a2 - 196)
                                                                              - 1 )
                          {
                            sub_72964B(a1: v135, a2: *(a2 - 193), a3: *(a2 - 192), a4: 1);
                            ++*(a2 - 193);
                          }
                          ++v135;
                        }
                        while ( v135 <= *(a2 - 194) );
                      }
                    }
                    break;
                  default:
                    break;
                }
              }
            }
            else if ( *(a2 - 192) != -1 )
            {
              v134 = *(a2 - 192);
              switch ( v134 )
              {
                case 0:
                  v133 = *((unsigned __int8 *)a2 - 852);
                  goto LABEL_171;
                case 1:
                  v133 = *((unsigned __int8 *)a2 - 851);
                  goto LABEL_171;
                case 2:
                  v133 = *((unsigned __int8 *)a2 - 850);
                  goto LABEL_171;
                case 3:
                  v133 = *((unsigned __int8 *)a2 - 849);
                  goto LABEL_171;
                default:
                  break;
              }
            }
            if ( (int)++*(a2 - 192) > 3 )
            {
              *((_BYTE *)a2 - 4) = 15;
              if ( *(a2 - 203) != 0 )
                sub_401BFB(a1: *(a2 - 203));
              *((_BYTE *)a2 - 4) = 5;
              std::string::_Tidy(a1: a2 - 51, a2: 1, Size: 0);
              v67 = *(a2 - 196);
              goto LABEL_181;
            }
          }
      }
      if ( v89 != 0 )
        ((void (*)(void))sub_401BFB)();
LABEL_129:
      if ( *(a2 - 204) != 0 )
      {
        v119 = (int *)sub_5C3828(a1: 0);
        v120 = v119;
        if ( v119 != nullptr )
        {
          v121 = *v119;
          v182 = 0;
          *(a2 - 198) = (*(int (__thiscall **)(int *))(v121 + 36))(a1: v120);
          v122 = *v120;
          v181 = 0;
          v123 = (*(int (__thiscall **)(int *))(v122 + 40))(a1: v120);
          sub_72013D(a1: *(a2 - 198) / 40 + 1);
          sub_720153(a1: v123 / 40 + 1);
        }
      }
      goto LABEL_132;
    }
LABEL_191:
    *(a2 - 233) = 0;
    *(a2 - 232) = 0;
    *(a2 - 231) = 0;
    *((_BYTE *)a2 - 4) = 35;
    *(a2 - 229) = 0;
    *(a2 - 228) = 0;
    *(a2 - 227) = 0;
    *((_BYTE *)a2 - 4) = 36;
    sub_8EC853(a1: a2 - 233);
    sub_8EC877(a1: a2 - 229);
    sub_729F44(a1: a2 - 233, a2: a2 - 229);
    sub_728E6E(a1);
    v144 = *(a2 - 205);
    if ( v144 > 0 )
    {
      v145 = a2 - 43;
      *(a2 - 195) = v144;
      do
      {
        sub_5BFE80(a1: v145[2], a2: v145[1]);
        sub_5BFE80(a1: *v145, a2: *(v145 - 1));
        v145 += 4;
        v132 = (*(a2 - 195))-- == 1;
      }
      while ( !v132 );
    }
    v146 = *(_DWORD *)a1;
    v180 = a2 - 86;
    (*(void (__thiscall **)(__int32))(v146 + 92))(a1);
    *((_BYTE *)a2 - 4) = 37;
    v147 = *(a2 - 82) != 0;
    *(int *)((char *)&dword_A83208 + a1) = v147;
    if ( v147 )
      sub_72EFC3(a1: a2 - 86);
    sub_72E15B(a1: a2 - 205, a2: *(int *)((char *)&dword_A8320C + a1), a3: *(int *)((char *)&dword_A8320C + a1 + 4));
    *(a2 - 224) = -1;
    *(a2 - 222) = -1;
    *(a2 - 225) = 0;
    *(a2 - 223) = 0;
    *(a2 - 221) = 0;
    *(a2 - 220) = 0;
    qmemcpy(v179, a2 - 225, sizeof(v179));
    v148 = sub_726B85(a1);
    sub_72F95A(a1: v148, a2: v179[0], a3: v179[1], a4: v179[2], a5: v179[3], a6: v179[4], a7: v179[5]);
    if ( *(a2 - 199) == 0 || sub_72BD92(a1: *(a2 - 202), a2: *(a2 - 199), a3: a2[3], a4: *(a2 - 219)) != 0 )
    {
      sub_73507B(a1: v180, a2: v181);
      sub_729EFA(a1: v180, a2: v181);
      sub_72C24C(a1);
      sub_731785(a1);
      if ( sub_8E78DB(a1: dword_E60884) == 20 || (v149 = sub_8E78DB(a1: dword_E60884)) == 33 )
      {
        v152 = j__malloc(Size: 0x90u);
        *(a2 - 219) = v152;
        *((_BYTE *)a2 - 4) = 38;
        if ( v152 != nullptr )
          v153 = sub_7D204A(a1: v180, a2: v181);
        else
          v153 = 0;
        *((_BYTE *)a2 - 4) = 37;
        v149 = sub_72A3C0(a1: v153);
      }
      v183 = 226883277;
      v154 = __readeflags();
      v203[1] = v154;
      v203[0] = v151;
      v202 = a1;
      v201 = (int)(a2 - 219);
      v200 = (int *)&v180;
      v199 = (void ***)v203;
      v155 = _InterlockedExchange((volatile __int32 *)&v200, (__int32)&v202);
      v156 = v201;
      v203[0] = v149;
      v201 = v150;
      v200 = (int *)v156;
      v199 = (void ***)&v199;
      v198 = v202;
      v197 = (void ***)v150;
      v196 = (unsigned int)&savedregs;
      v195 = v156;
      v157 = _InterlockedExchange(&v198, (__int32)&v198);
      v200 = (int *)((char *)v200 + 1893170273);
      ++v200;
      v200 = (int *)((char *)v200 - 1893170273);
      v199 = (void ***)&savedregs;
      v198 = v156;
      v158 = _InterlockedExchange(&v198, (__int32)&v198);
      v199 = (void ***)v157;
      v196 = (unsigned int)&savedregs;
      v198 = v158;
      v197 = (void ***)&savedregs;
      v159 = _InterlockedExchange((volatile __int32 *)&v199, (__int32)&v199);
      v200 = a2 - 219;
      v199 = (void ***)v155;
      v198 = v149;
      v197 = (void ***)v149;
      v196 = v150;
      v194 = v149;
      v195 = (__int32)v200;
      v160 = v150 ^ (unsigned int)&v198;
      v196 ^= v160;
      savedregs = 18801589;
      v209 = v196 ^ v160;
      v206 = 18801589;
      v205 = (__int32)v200;
      v204 = v159;
      v161 = v196 ^ v160 ^ (unsigned int)&retaddr;
      v209 ^= v161;
      v162 = v209 ^ v161;
      v209 = v159;
      v208 = v200;
      v207 = (void ***)v200;
      _InterlockedExchange((volatile __int32 *)&v207, (__int32)&v207);
      v206 = -102553856;
      v163 = v209;
      v164 = (__int32 *)retaddr;
      v165 = savedregs ^ (unsigned int)&a3;
      savedregs = (unsigned int)&a3;
      v209 = -206683502;
      v208 = (__int32 *)&savedregs;
      v207 = (void ***)v163;
      v166 = _InterlockedExchange(&v209, (__int32)&v209);
      v207 = (void ***)v162;
      v208 = &v209;
      savedregs = (unsigned int)&savedregs;
      v209 = (__int32)(&savedregs + 2);
      _InterlockedExchange(&v209, (__int32)&savedregs);
      savedregs = (unsigned int)&savedregs;
      retaddr = (void ***)&savedregs;
      v209 = (v166 & 0xFFFFF000) + 20;
      v167 = v209;
      v208 = (__int32 *)((unsigned int)&a3 ^ v165);
      v207 = (void ***)v209;
      v168 = _InterlockedExchange((volatile __int32 *)&v207, (__int32)&v207);
      v209 = (__int32)v164;
      v169 = v168 - 594429871 + 819914119;
      v208 = v164;
      v170 = (__int32)v164;
      v207 = (void ***)&savedregs;
      v206 = (__int32)v164;
      v205 = (__int32)v164;
      v171 = _InterlockedExchange(&v205, (__int32)&v207);
      v207 = (void ***)v206;
      if ( v167 != *(_DWORD *)(v169 + 140) )
      {
        v207 = (void ***)v162;
        v206 = v170;
        v205 = v163;
        _InterlockedExchange(&v205, (__int32)&v205);
        v206 = (__int32)&savedregs;
        _InterlockedExchange(&v206, (__int32)&savedregs);
        *(_DWORD *)(v169 - 1459316053 + 1459316193) = v167 - 980430104;
        v206 = v171;
        *(_DWORD *)(v169 - 1459316053 + 1459316193) += 980430104;
        v162 = (__int32)v207;
        v206 = (__int32)&savedregs;
        v205 = 1834962989;
        v207 = (void ***)v170;
        v171 = 170;
        while ( v171 != 0 )
        {
          v207 = (void ***)v170;
          v206 = v171;
          v205 = v162;
          *(_DWORD *)(v169 + 4 * v171 + 559092835 - 559092691) += v167;
          v162 = v205;
          v172 = v206;
          v205 = v167;
          v173 = _InterlockedExchange(&v205, (__int32)&v207);
          v170 = v206;
          v206 = v169;
          v204 = 1;
          v203[17] = v162;
          v171 = v172 - 1890720813 + 1890720812;
          v205 = v173;
          v174 = v173 ^ (unsigned int)&v207;
          v205 ^= v174;
          v167 = v205 ^ v174;
        }
      }
      v207 = (void ***)a8;
      v175 = a8;
      v206 = v170;
      v205 = v169;
      v204 = v167;
      _InterlockedExchange(&v204, (__int32)&v204);
      v204 = (__int32)&v207;
      v205 = v206;
      v209 = v206;
      v208 = (__int32 *)(v175 + 1655197812);
      v207 = (void ***)v175;
      v206 = 738579392;
      v176 = _InterlockedExchange(&v206, (__int32)&v208);
      v177 = (__int32)v207 - v176 - 916618420;
      v207 = (void ***)v208;
      v178 = (__int32)v208;
      v206 = (__int32)&savedregs;
      _InterlockedExchange(&v206, (__int32)&savedregs);
      v207 = (void ***)v177;
      v206 = v178;
      v205 = v171;
      v204 = (__int32)&savedregs;
      while ( _InterlockedCompareExchange((volatile signed __int32 *)(v178 + 124), 1, 0) != 0 )
        ;
      v207 = (void ***)v162;
      JUMPOUT(0x11FD0AA);
    }
    *((_BYTE *)a2 - 4) = 36;
    std::string::_Tidy(a1: a2 - 86, a2: 1, Size: 0);
    *((_BYTE *)a2 - 4) = 35;
    sub_6A4F48(a1: a2 - 229);
    *((_BYTE *)a2 - 4) = 5;
    sub_6A4F48(a1: a2 - 233);
    *((_BYTE *)a2 - 4) = 4;
    sub_48D93D(a1: v180, a2: v181);
    *((_BYTE *)a2 - 4) = 3;
    std::string::_Tidy(a1: a2 - 72, a2: 1, Size: 0);
    *((_BYTE *)a2 - 4) = 1;
    sub_9E0611(a1: *(a2 - 201));
    *((_BYTE *)a2 - 4) = 0;
    std::string::_Tidy(a1: a2 - 79, a2: 1, Size: 0);
    *(a2 - 1) = -1;
    sub_A35800(a1: a2 - 97);
  }
  return sub_9DB5CB();
}