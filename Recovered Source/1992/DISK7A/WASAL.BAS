10 PRINT"  "
1000 REM sound / music maker
1010 REM
1020 REM
1030 REM
1040 REM sound finished when :-
1050 REM $04fe (hi) = 0 and
1060 REM $04fc (lo) = 0
1070 :
1080 DIM n(28)
1090 :
1100 RESTORE 1520
1110 :
1120 FOR a=0 TO 28
1130 READ n(a)
1140 NEXT
1150 :
1160 VOL 8
1170 :
1180 RESTORE 1620
1190 :
1200 REM tune data at 10000
1210 :
1220 DO
1230 :
1240 READ a$,l%
1250 :
1260 IF a$="end" THEN GOTO 1840
1261 IF a$="rest" THEN n%=28:GOTO1410
1270 :
1280 PRINT"  "
1290 PRINT"  note  = ";LEFT$(a$,1)
1300 PRINT"  octave   ";RIGHT$(a$,1)
1310 PRINT"  note length   = ";l%
1320 :
1330 o%=ASC("4")-ASC(RIGHT$(a$,1))
1340 :
1350 n%=ASC("g")-(ASC(LEFT$(a$,1)))
1351 PRINTn%
1360 :
1370 n%=n%+o%*7
1380 :
1381 PRINTn%,o%
1390 hn%=n(n%)/256
1400 ln%=n(n%)-hn%*256
1401 PRINT"lo = ";ln%;" * hi = ";hn%;"    "
1410 SOUND 1,n(n%),l%*2
1420 :
1430 DO
1440 a=PEEK(1276):b=PEEK(1278)
1450 LOOP UNTIL a=0 AND b=0
1460 :
1470 REM  get a$:if a$=""then 1470
1480 LOOP UNTIL 0
1490 :
1500 FOR t=0 TO l%:NEXT
1510 :
1520 REM data for sound chip
1530 :
1540 DATA 955,906,855,762
1550 DATA 679,641,571,508
1560 DATA 453,428,381,339
1570 DATA 320,285,254,226
1580 DATA 214,190,170,141
1590 DATA 140,127,113,107
1600 DATA 95,85,80,71
1601 DATA 0
1610 :
1620 REM tune data
1630 REM in form :-
1640 REM a1,0
1650 REM note/octave,length
1660 :
1690 :
1700 DATA c3,6,g3,3,g3,3
1710 DATA g3,3,a3,3,g3,6
1720 DATA b3,6,c3,6
1780 :
1790 :
1800 DATA end,1
1810 :
1820 REM **************************
1830 :
1840 REM end
1850 :
1860 VOL 0
1870 :
1880 STOP
