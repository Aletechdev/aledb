#=GENOME_DIFF	1.0
#=TITLE	breseq
#=CREATED	22:18:49 19 Mar 2025
#=PROGRAM	breseq 0.35.4 revision f352f80f4bc9
#=COMMAND	/usr/bin/breseq-0.35.4-Linux-x86_64/bin/breseq -j 2 --consensus-frequency-cutoff=0.75 --require-match-fraction=0.95 -o breseq_processes/0 -r /var/data/NC_000913_3.gb /var/alemutpipe-outputs/good/BOP374E_I2_S318_R1_001.good.fq.gz /var/alemutpipe-outputs/good/BOP374E_I2_S318_R2_001.good.fq.gz
#=REFSEQ	/var/data/NC_000913_3.gb
#=READSEQ	/var/alemutpipe-outputs/good/BOP374E_I2_S318_R1_001.good.fq.gz
#=READSEQ	/var/alemutpipe-outputs/good/BOP374E_I2_S318_R2_001.good.fq.gz
#=CONVERTED-BASES	561220830
#=CONVERTED-READS	4127630
#=INPUT-BASES	561220830
#=INPUT-READS	4127630
#=MAPPED-BASES	559335850
#=MAPPED-READS	4114308
DEL	1	.	NC_000913	257908	776	gene_name=insB9–[crl]	gene_product=insB9,insA9,[crl]	genes_inactivated=insB9,insA9,crl	html_gene_name=<i>insB9</i>&#8211;<i>[crl]</i>	html_gene_product=<i>insB9</i>, <i>insA9</i>, <i>[crl]</i>	html_mutation=&Delta;776&nbsp;bp	html_position=257,908	html_seq_id=NC_000913	locus_tag=[b4710]–[b0240]	locus_tags_inactivated=b4710,b4709,b0240	mutation_category=large_deletion	position_end=258683	position_start=257908	ref_seq=776-bp
SNP	2	.	NC_000913	508670	C	gene_name=ybaQ/copA	gene_position=intergenic (+111/+205)	gene_product=putative DNA-binding transcriptional regulator YbaQ/Cu(+) exporting P-type ATPase	gene_strand=>/<	genes_promoter=copA	html_gene_name=<i>ybaQ</i>&nbsp;&rarr;&nbsp;/&nbsp;&larr;&nbsp;<i>copA</i>	html_gene_product=putative DNA&#8209;binding transcriptional regulator YbaQ/Cu(+) exporting P&#8209;type ATPase	html_mutation=T&rarr;C	html_mutation_annotation=intergenic&nbsp;(+111/+205)	html_position=508,670	html_seq_id=NC_000913	locus_tag=b0483/b0484	locus_tags_promoter=b0484	mutation_category=snp_intergenic	position_end=508670	position_start=508670	ref_seq=T	snp_type=intergenic
DEL	3	.	NC_000913	1978503	776	gene_name=insB-5–insA-5	gene_product=insB-5,insA-5	genes_inactivated=insB-5,insA-5	html_gene_name=<i>insB&#8209;5</i>&#8211;<i>insA&#8209;5</i>	html_gene_product=<i>insB&#8209;5</i>, <i>insA&#8209;5</i>	html_mutation=&Delta;776&nbsp;bp	html_position=1,978,503	html_seq_id=NC_000913	locus_tag=[b1893]–[b1894]	locus_tags_inactivated=b1893,b1894	mutation_category=large_deletion	position_end=1979278	position_start=1978503	ref_seq=776-bp
DEL	4	.	NC_000913	2173363	2	gene_name=gatC	gene_position=pseudogene (915-916/1358 nt)	gene_product=galactitol-specific PTS enzyme IIC component	gene_strand=<	genes_inactivated=gatC	html_gene_name=<i>gatC</i>&nbsp;&larr;	html_gene_product=galactitol&#8209;specific PTS enzyme IIC component	html_mutation=&Delta;2&nbsp;bp	html_mutation_annotation=pseudogene&nbsp;(915&#8209;916/1358&nbsp;nt)	html_position=2,173,363	html_seq_id=NC_000913	locus_tag=b2092	locus_tags_inactivated=b2092	mutation_category=small_indel	position_end=2173364	position_start=2173363	ref_seq=CC
SNP	5	.	NC_000913	2407235	C	gene_name=lrhA/alaA	gene_position=intergenic (-594/-326)	gene_product=DNA-binding transcriptional dual regulator LrhA/glutamate--pyruvate aminotransferase AlaA	gene_strand=</>	html_gene_name=<i>lrhA</i>&nbsp;&larr;&nbsp;/&nbsp;&rarr;&nbsp;<i>alaA</i>	html_gene_product=DNA&#8209;binding transcriptional dual regulator LrhA/glutamate&#8209;&#8209;pyruvate aminotransferase AlaA	html_mutation=G&rarr;C	html_mutation_annotation=intergenic&nbsp;(&#8209;594/&#8209;326)	html_position=2,407,235	html_seq_id=NC_000913	locus_tag=b2289/b2290	mutation_category=snp_intergenic	position_end=2407235	position_start=2407235	ref_seq=G	snp_type=intergenic
MOB	6	.	NC_000913	2536312	IS186	-1	6	del_end=1	del_start=1	gene_name=crr	gene_position=coding (479-484/510 nt)	gene_product=Enzyme IIA(Glc)	gene_strand=>	genes_overlapping=crr	html_gene_name=<i>crr</i>&nbsp;&rarr;	html_gene_product=Enzyme IIA(Glc)	html_mutation=&Delta;1&nbsp;bp&nbsp;::&nbsp;IS<i>186</i>&nbsp;(&#8211;)&nbsp;+6&nbsp;bp&nbsp;::&nbsp;&Delta;1&nbsp;bp	html_mutation_annotation=coding&nbsp;(479&#8209;484/510&nbsp;nt)	html_position=2,536,312	html_seq_id=NC_000913	locus_tag=b2417	locus_tags_overlapping=b2417	mutation_category=mobile_element_insertion	position_end=2536317	position_start=2536312	ref_seq=GTGAAA
SNP	7	.	NC_000913	2742299	C	aa_new_seq=A	aa_position=142	aa_ref_seq=V	codon_new_seq=GCC	codon_number=142	codon_position=2	codon_ref_seq=GTC	gene_name=yfiR	gene_position=425	gene_product=DUF4154 domain-containing protein YfiR	gene_strand=>	genes_overlapping=yfiR	html_gene_name=<i>yfiR</i>&nbsp;&rarr;	html_gene_product=DUF4154 domain&#8209;containing protein YfiR	html_mutation=T&rarr;C	html_mutation_annotation=<font class="snp_type_nonsynonymous">V142A</font>&nbsp;(G<font class="mutation_in_codon">T</font>C&rarr;G<font class="mutation_in_codon">C</font>C)&nbsp;	html_position=2,742,299	html_seq_id=NC_000913	locus_tag=b2603	locus_tags_overlapping=b2603	mutation_category=snp_nonsynonymous	position_end=2742299	position_start=2742299	ref_seq=T	snp_type=nonsynonymous	transl_table=11
SNP	8	.	NC_000913	2934116	A	gene_name=fucA/fucP	gene_position=intergenic (-428/-119)	gene_product=L-fuculose-phosphate aldolase/L-fucose:H(+) symporter	gene_strand=</>	html_gene_name=<i>fucA</i>&nbsp;&larr;&nbsp;/&nbsp;&rarr;&nbsp;<i>fucP</i>	html_gene_product=L&#8209;fuculose&#8209;phosphate aldolase/L&#8209;fucose:H(+) symporter	html_mutation=T&rarr;A	html_mutation_annotation=intergenic&nbsp;(&#8209;428/&#8209;119)	html_position=2,934,116	html_seq_id=NC_000913	locus_tag=b2800/b2801	mutation_category=snp_intergenic	position_end=2934116	position_start=2934116	ref_seq=T	snp_type=intergenic
INS	9	.	NC_000913	3560455	G	gene_name=glpR	gene_position=pseudogene (151/758 nt)	gene_product=DNA-binding transcriptional repressor GlpR	gene_strand=<	genes_inactivated=glpR	html_gene_name=<i>glpR</i>&nbsp;&larr;	html_gene_product=DNA&#8209;binding transcriptional repressor GlpR	html_mutation=+G	html_mutation_annotation=pseudogene&nbsp;(151/758&nbsp;nt)	html_position=3,560,455	html_seq_id=NC_000913	locus_tag=b3423	locus_tags_inactivated=b3423	mutation_category=small_indel	position_end=3560455	position_start=3560455	ref_seq=C
DEL	10	.	NC_000913	3992385	8	gene_name=cyaA	gene_position=coding (1233-1240/2547 nt)	gene_product=adenylate cyclase	gene_strand=>	genes_inactivated=cyaA	html_gene_name=<i>cyaA</i>&nbsp;&rarr;	html_gene_product=adenylate cyclase	html_mutation=&Delta;8&nbsp;bp	html_mutation_annotation=coding&nbsp;(1233&#8209;1240/2547&nbsp;nt)	html_position=3,992,385	html_seq_id=NC_000913	locus_tag=b3806	locus_tags_inactivated=b3806	mutation_category=small_indel	position_end=3992392	position_start=3992385	ref_seq=TCCGCAGG
INS	11	.	NC_000913	4296381	GC	gene_name=gltP/yjcO	gene_position=intergenic (+587/+55)	gene_product=glutamate/aspartate : H(+) symporter GltP/Sel1 repeat-containing protein YjcO	gene_strand=>/<	genes_promoter=yjcO	html_gene_name=<i>gltP</i>&nbsp;&rarr;&nbsp;/&nbsp;&larr;&nbsp;<i>yjcO</i>	html_gene_product=glutamate/aspartate : H(+) symporter GltP/Sel1 repeat&#8209;containing protein YjcO	html_mutation=+GC	html_mutation_annotation=intergenic&nbsp;(+587/+55)	html_position=4,296,381	html_seq_id=NC_000913	locus_tag=b4077/b4078	locus_tags_promoter=b4078	mutation_category=small_indel	position_end=4296381	position_start=4296381	ref_seq=C
UN	12	.	NC_000913	15516	16604
UN	13	.	NC_000913	19931	20433
UN	14	.	NC_000913	122998	127565
UN	15	.	NC_000913	223877	224651
UN	16	.	NC_000913	224655	224660
UN	17	.	NC_000913	225006	225454
UN	18	.	NC_000913	225852	225895
UN	19	.	NC_000913	226140	226169
UN	20	.	NC_000913	226429	226477
UN	21	.	NC_000913	226731	226839
UN	22	.	NC_000913	227122	228556
UN	23	.	NC_000913	228812	228874
UN	24	.	NC_000913	257908	258683
UN	25	.	NC_000913	270653	271165
UN	26	.	NC_000913	274088	275018
UN	27	.	NC_000913	279294	279812
UN	28	.	NC_000913	290767	291271
UN	29	.	NC_000913	315363	316349
UN	30	.	NC_000913	381385	382464
UN	31	.	NC_000913	391830	391830
UN	32	.	NC_000913	391832	391832
UN	33	.	NC_000913	391837	392838
UN	34	.	NC_000913	525996	526590
UN	35	.	NC_000913	566898	566898
UN	36	.	NC_000913	566905	567911
UN	37	.	NC_000913	574718	575673
UN	38	.	NC_000913	608136	609223
UN	39	.	NC_000913	687978	688933
UN	40	.	NC_000913	729930	730018
UN	41	.	NC_000913	732120	732159
UN	42	.	NC_000913	950396	954411
UN	43	.	NC_000913	1050175	1050271
UN	44	.	NC_000913	1094376	1095374
UN	45	.	NC_000913	1097444	1097444
UN	46	.	NC_000913	1097446	1097446
UN	47	.	NC_000913	1097448	1097454
UN	48	.	NC_000913	1299499	1300697
UN	49	.	NC_000913	1396150	1396150
UN	50	.	NC_000913	1396155	1397111
UN	51	.	NC_000913	1432403	1432524
UN	52	.	NC_000913	1432784	1433067
UN	53	.	NC_000913	1433071	1433071
UN	54	.	NC_000913	1433501	1433534
UN	55	.	NC_000913	1433786	1433947
UN	56	.	NC_000913	1433951	1433951
UN	57	.	NC_000913	1434206	1434223
UN	58	.	NC_000913	1468036	1469112
UN	59	.	NC_000913	1469114	1469114
UN	60	.	NC_000913	1469423	1470399
UN	61	.	NC_000913	1528450	1529050
UN	62	.	NC_000913	1571001	1571217
UN	63	.	NC_000913	1571521	1571671
UN	64	.	NC_000913	1633085	1633100
UN	65	.	NC_000913	1633349	1633510
UN	66	.	NC_000913	1633763	1633795
UN	67	.	NC_000913	1634220	1634514
UN	68	.	NC_000913	1634773	1634900
UN	69	.	NC_000913	1650972	1651419
UN	70	.	NC_000913	1978503	1979278
UN	71	.	NC_000913	2066309	2066338
UN	72	.	NC_000913	2066850	2067177
UN	73	.	NC_000913	2069067	2070147
UN	74	.	NC_000913	2101870	2102825
UN	75	.	NC_000913	2170300	2171305
UN	76	.	NC_000913	2289050	2289992
UN	77	.	NC_000913	2304681	2304681
UN	78	.	NC_000913	2304683	2304688
UN	79	.	NC_000913	2304690	2304692
UN	80	.	NC_000913	2304694	2304694
UN	81	.	NC_000913	2514402	2515490
UN	82	.	NC_000913	2726177	2729114
UN	83	.	NC_000913	2729686	2730821
UN	84	.	NC_000913	2731200	2731247
UN	85	.	NC_000913	2731252	2731253
UN	86	.	NC_000913	2996486	2997568
UN	87	.	NC_000913	3130264	3131213
UN	88	.	NC_000913	3186221	3187296
UN	89	.	NC_000913	3365683	3366627
UN	90	.	NC_000913	3423790	3424526
UN	91	.	NC_000913	3424783	3426714
UN	92	.	NC_000913	3426716	3426716
UN	93	.	NC_000913	3426946	3428427
UN	94	.	NC_000913	3428678	3428792
UN	95	.	NC_000913	3470296	3470609
UN	96	.	NC_000913	3470867	3470907
UN	97	.	NC_000913	3583550	3584068
UN	98	.	NC_000913	3619402	3620951
UN	99	.	NC_000913	3621210	3622168
UN	100	.	NC_000913	3652160	3653112
UN	101	.	NC_000913	3666534	3666752
UN	102	.	NC_000913	3667066	3667210
UN	103	.	NC_000913	3731142	3734592
UN	104	.	NC_000913	3762393	3763942
UN	105	.	NC_000913	3764210	3765154
UN	106	.	NC_000913	3933835	3937111
UN	107	.	NC_000913	3941779	3941886
UN	108	.	NC_000913	3942158	3943272
UN	109	.	NC_000913	3943519	3943551
UN	110	.	NC_000913	3943716	3943859
UN	111	.	NC_000913	3944187	3945439
UN	112	.	NC_000913	3945696	3945769
UN	113	.	NC_000913	3946043	3946096
UN	114	.	NC_000913	3946354	3946492
UN	115	.	NC_000913	3946820	3946820
UN	116	.	NC_000913	3992385	3992392
UN	117	.	NC_000913	4035289	4035612
UN	118	.	NC_000913	4035866	4036972
UN	119	.	NC_000913	4037220	4037347
UN	120	.	NC_000913	4037531	4037698
UN	121	.	NC_000913	4037968	4038563
UN	122	.	NC_000913	4038864	4039257
UN	123	.	NC_000913	4039525	4040477
UN	124	.	NC_000913	4144054	4147084
UN	125	.	NC_000913	4166417	4168089
UN	126	.	NC_000913	4168694	4171513
UN	127	.	NC_000913	4171516	4171517
UN	128	.	NC_000913	4176366	4176407
UN	129	.	NC_000913	4176412	4176412
UN	130	.	NC_000913	4176658	4176977
UN	131	.	NC_000913	4208253	4209598
UN	132	.	NC_000913	4209861	4209890
UN	133	.	NC_000913	4210153	4213040
UN	134	.	NC_000913	4296178	4296322
UN	135	.	NC_000913	4308543	4311987
UN	136	.	NC_000913	4498312	4499383
UN	137	.	NC_000913	4507585	4508558
