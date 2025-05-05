#=GENOME_DIFF	1.0
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
DEL	1	41,52	NC_000913	257908	776
SNP	2	13	NC_000913	508670	C
DEL	3	43,58	NC_000913	1978503	776
DEL	4	23,24	NC_000913	2173363	2
SNP	5	25	NC_000913	2407235	C
MOB	6	59,60	NC_000913	2536312	IS186	-1	6	del_end=1	del_start=1
SNP	7	26	NC_000913	2742299	C
SNP	8	27	NC_000913	2934116	A
INS	9	31	NC_000913	3560455	G
DEL	10	47,61	NC_000913	3992385	8
INS	11	36,37	NC_000913	4296381	GC
RA	12	.	NC_000913	451095	0	G	C	bias_e_value=0.610375	bias_p_value=1.31499e-07	consensus_reject=FREQUENCY_CUTOFF	consensus_score=270.3	fisher_strand_p_value=6.63082e-09	frequency=2.069e-01	ks_quality_p_value=1	major_base=G	major_cov=57/35	major_frequency=7.931e-01	minor_base=C	minor_cov=0/24	new_cov=0/24	polymorphism_frequency=2.069e-01	polymorphism_score=23.2	prediction=polymorphism	ref_cov=57/35	total_cov=57/65
RA	13	.	NC_000913	508670	0	T	C	consensus_score=360.4	frequency=1	major_base=C	major_cov=53/45	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=53/45	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=53/45
RA	14	.	NC_000913	558752	0	T	C	bias_e_value=0.00896484	bias_p_value=1.93139e-09	consensus_reject=FREQUENCY_CUTOFF	consensus_score=173.0	fisher_strand_p_value=7.96332e-11	frequency=3.091e-01	ks_quality_p_value=1	major_base=T	major_cov=46/30	major_frequency=6.909e-01	minor_base=C	minor_cov=0/34	new_cov=0/34	polymorphism_frequency=3.091e-01	polymorphism_score=36.8	prediction=polymorphism	ref_cov=46/30	total_cov=46/64
RA	15	.	NC_000913	847955	0	G	A	bias_e_value=0.00714282	bias_p_value=1.53885e-09	consensus_reject=FREQUENCY_CUTOFF	consensus_score=179.9	fisher_strand_p_value=6.28347e-11	frequency=2.752e-01	ks_quality_p_value=1	major_base=G	major_cov=51/28	major_frequency=7.248e-01	minor_base=A	minor_cov=0/30	new_cov=0/30	polymorphism_frequency=2.752e-01	polymorphism_score=20.5	prediction=polymorphism	ref_cov=51/28	total_cov=51/66
RA	16	.	NC_000913	1191559	0	A	G	bias_e_value=0.0254058	bias_p_value=5.47345e-09	consensus_reject=FREQUENCY_CUTOFF	consensus_score=257.0	fisher_strand_p_value=2.3627e-10	frequency=2.435e-01	ks_quality_p_value=1	major_base=A	major_cov=32/55	major_frequency=7.565e-01	minor_base=G	minor_cov=28/0	new_cov=28/0	polymorphism_frequency=2.435e-01	polymorphism_score=25.5	prediction=polymorphism	ref_cov=32/55	total_cov=60/55
RA	17	.	NC_000913	1428762	0	T	C	bias_e_value=3.1597e-05	bias_p_value=6.80727e-12	consensus_reject=FREQUENCY_CUTOFF	consensus_score=180.4	fisher_strand_p_value=2.26019e-13	frequency=2.887e-01	ks_quality_p_value=1	major_base=T	major_cov=53/16	major_frequency=7.113e-01	minor_base=C	minor_cov=0/28	new_cov=0/28	polymorphism_frequency=2.887e-01	polymorphism_score=40.3	prediction=polymorphism	ref_cov=53/16	total_cov=53/44
RA	18	.	NC_000913	1428765	0	T	C	bias_e_value=6.34682e-09	bias_p_value=1.36736e-15	consensus_reject=FREQUENCY_CUTOFF	consensus_score=118.4	fisher_strand_p_value=3.5995e-17	frequency=3.579e-01	ks_quality_p_value=0.976884	major_base=T	major_cov=51/10	major_frequency=6.421e-01	minor_base=C	minor_cov=0/34	new_cov=0/34	polymorphism_frequency=3.579e-01	polymorphism_score=75.1	prediction=polymorphism	ref_cov=51/10	total_cov=51/44
RA	19	.	NC_000913	1502770	0	T	C	bias_e_value=0.190783	bias_p_value=4.11024e-08	consensus_reject=FREQUENCY_CUTOFF	consensus_score=148.1	fisher_strand_p_value=1.95221e-09	frequency=2.637e-01	ks_quality_p_value=1	major_base=T	major_cov=45/22	major_frequency=7.363e-01	minor_base=C	minor_cov=0/24	new_cov=0/24	polymorphism_frequency=2.637e-01	polymorphism_score=36.3	prediction=polymorphism	ref_cov=45/22	total_cov=45/46
RA	20	.	NC_000913	1637686	0	C	G	bias_e_value=70.8699	bias_p_value=1.52683e-05	consensus_reject=FREQUENCY_CUTOFF	consensus_score=135.7	fisher_strand_p_value=1.03281e-06	frequency=2.727e-01	ks_quality_p_value=1	major_base=C	major_cov=24/32	major_frequency=7.273e-01	minor_base=G	minor_cov=21/0	new_cov=21/0	polymorphism_frequency=2.727e-01	polymorphism_score=20.6	prediction=polymorphism	ref_cov=24/32	total_cov=60/32
RA	21	.	NC_000913	2162881	0	G	C	bias_e_value=2.64056	bias_p_value=5.68883e-07	consensus_reject=FREQUENCY_CUTOFF	consensus_score=201.2	fisher_strand_p_value=3.11108e-08	frequency=2.111e-01	ks_quality_p_value=1	major_base=G	major_cov=48/23	major_frequency=7.889e-01	minor_base=C	minor_cov=0/19	new_cov=0/19	polymorphism_frequency=2.111e-01	polymorphism_score=17.2	prediction=polymorphism	ref_cov=48/23	total_cov=49/49
RA	22	.	NC_000913	2162882	0	T	C	bias_e_value=12.7475	bias_p_value=2.74634e-06	consensus_reject=FREQUENCY_CUTOFF	consensus_score=220.5	fisher_strand_p_value=1.65287e-07	frequency=2.041e-01	ks_quality_p_value=1	major_base=T	major_cov=49/29	major_frequency=7.959e-01	minor_base=C	minor_cov=0/20	new_cov=0/20	polymorphism_frequency=2.041e-01	polymorphism_score=19.6	prediction=polymorphism	ref_cov=49/29	total_cov=49/49
RA	23	.	NC_000913	2173361	0	C	.	consensus_score=429.8	frequency=1	major_base=.	major_cov=31/51	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=31/51	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=31/51
RA	24	.	NC_000913	2173362	0	C	.	consensus_score=429.8	frequency=1	major_base=.	major_cov=31/51	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=31/51	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=31/51
RA	25	.	NC_000913	2407235	0	G	C	consensus_score=415.0	frequency=1	major_base=C	major_cov=48/63	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=48/63	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=48/63
RA	26	.	NC_000913	2742299	0	T	C	consensus_score=416.6	frequency=1	major_base=C	major_cov=42/70	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=42/70	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=42/70
RA	27	.	NC_000913	2934116	0	T	A	consensus_score=437.0	frequency=1	major_base=A	major_cov=39/69	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=39/69	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=39/69
RA	28	.	NC_000913	3032307	0	C	T	bias_e_value=0.00386218	bias_p_value=8.3207e-10	consensus_reject=FREQUENCY_CUTOFF	consensus_score=204.6	fisher_strand_p_value=3.3109e-11	frequency=2.880e-01	ks_quality_p_value=1	major_base=C	major_cov=37/52	major_frequency=7.120e-01	minor_base=T	minor_cov=36/0	new_cov=36/0	polymorphism_frequency=2.880e-01	polymorphism_score=24.8	prediction=polymorphism	ref_cov=37/52	total_cov=96/52
RA	29	.	NC_000913	3325363	0	C	G	bias_e_value=0.0145513	bias_p_value=3.13493e-09	consensus_reject=FREQUENCY_CUTOFF	consensus_score=263.6	fisher_strand_p_value=1.32007e-10	frequency=2.039e-01	ks_quality_p_value=1	major_base=C	major_cov=21/61	major_frequency=7.961e-01	minor_base=G	minor_cov=21/0	new_cov=21/0	polymorphism_frequency=2.039e-01	polymorphism_score=18.3	prediction=polymorphism	ref_cov=21/61	total_cov=50/61
RA	30	.	NC_000913	3400539	0	G	A	bias_e_value=0.000884263	bias_p_value=1.90506e-10	consensus_reject=FREQUENCY_CUTOFF	consensus_score=165.9	fisher_strand_p_value=7.14451e-12	frequency=2.897e-01	ks_quality_p_value=1	major_base=G	major_cov=51/25	major_frequency=7.103e-01	minor_base=A	minor_cov=0/31	new_cov=0/31	polymorphism_frequency=2.897e-01	polymorphism_score=27.6	prediction=polymorphism	ref_cov=51/25	total_cov=51/67
RA	31	.	NC_000913	3560455	1	.	G	consensus_score=482.9	frequency=1	major_base=G	major_cov=65/64	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=65/64	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=65/64
RA	32	.	NC_000913	3659163	0	A	G	bias_e_value=0.0013271	bias_p_value=2.85911e-10	consensus_reject=FREQUENCY_CUTOFF	consensus_score=211.8	fisher_strand_p_value=1.08949e-11	frequency=2.696e-01	ks_quality_p_value=1	major_base=A	major_cov=29/55	major_frequency=7.304e-01	minor_base=G	minor_cov=31/0	new_cov=31/0	polymorphism_frequency=2.696e-01	polymorphism_score=38.3	prediction=polymorphism	ref_cov=29/55	total_cov=60/55
RA	33	.	NC_000913	3659164	0	A	G	bias_e_value=0.164569	bias_p_value=3.54548e-08	consensus_reject=FREQUENCY_CUTOFF	consensus_score=241.9	fisher_strand_p_value=1.67165e-09	frequency=2.261e-01	ks_quality_p_value=1	major_base=A	major_cov=34/55	major_frequency=7.739e-01	minor_base=G	minor_cov=26/0	new_cov=26/0	polymorphism_frequency=2.261e-01	polymorphism_score=24.3	prediction=polymorphism	ref_cov=34/55	total_cov=60/55
RA	34	.	NC_000913	3837264	0	C	G	bias_e_value=7.8471e-09	bias_p_value=1.69058e-15	consensus_reject=FREQUENCY_CUTOFF	consensus_score=236.5	fisher_strand_p_value=4.37196e-17	frequency=2.727e-01	ks_quality_p_value=1	major_base=C	major_cov=13/67	major_frequency=7.273e-01	minor_base=G	minor_cov=30/0	new_cov=30/0	polymorphism_frequency=2.727e-01	polymorphism_score=32.7	prediction=polymorphism	ref_cov=13/67	total_cov=44/68
RA	35	.	NC_000913	4296060	0	C	T	bias_e_value=4610720	bias_p_value=0.993337	consensus_reject=FREQUENCY_CUTOFF	consensus_score=188.1	fisher_strand_p_value=1	frequency=2.797e-01	ks_quality_p_value=0.886805	major_base=C	major_cov=39/46	major_frequency=7.203e-01	minor_base=T	minor_cov=15/18	new_cov=15/18	polymorphism_frequency=2.797e-01	polymorphism_score=94.6	prediction=polymorphism	ref_cov=39/46	total_cov=54/64
RA	36	.	NC_000913	4296380	1	.	C	bias_e_value=4641350	bias_p_value=0.999936	consensus_score=274.0	fisher_strand_p_value=1	frequency=1	ks_quality_p_value=0.988672	major_base=C	major_cov=38/41	major_frequency=9.875e-01	minor_base=T	minor_cov=0/1	new_cov=38/41	polymorphism_frequency=9.875e-01	polymorphism_score=-4.0	prediction=consensus	ref_cov=0/0	total_cov=38/42
RA	37	.	NC_000913	4296380	2	.	G	consensus_score=288.9	frequency=1	major_base=G	major_cov=38/44	major_frequency=1.000e+00	minor_base=N	minor_cov=0/0	new_cov=38/44	polymorphism_frequency=1.000e+00	polymorphism_score=NA	prediction=consensus	ref_cov=0/0	total_cov=38/44
RA	38	.	NC_000913	4338130	0	G	C	bias_e_value=0.00759385	bias_p_value=1.63602e-09	consensus_reject=FREQUENCY_CUTOFF	consensus_score=144.7	fisher_strand_p_value=6.69769e-11	frequency=2.949e-01	ks_quality_p_value=1	major_base=G	major_cov=42/13	major_frequency=7.051e-01	minor_base=C	minor_cov=0/23	new_cov=0/23	polymorphism_frequency=2.949e-01	polymorphism_score=22.3	prediction=polymorphism	ref_cov=42/13	total_cov=42/45
RA	39	.	NC_000913	4352345	0	T	C	bias_e_value=506.658	bias_p_value=0.000109155	consensus_reject=FREQUENCY_CUTOFF	consensus_score=199.6	fisher_strand_p_value=8.62112e-06	frequency=2.321e-01	ks_quality_p_value=1	major_base=T	major_cov=36/50	major_frequency=7.679e-01	minor_base=C	minor_cov=0/26	new_cov=0/26	polymorphism_frequency=2.321e-01	polymorphism_score=19.0	prediction=polymorphism	ref_cov=36/50	total_cov=36/76
MC	40	.	NC_000913	122974	127601	0	0	left_inside_cov=45	left_outside_cov=48	right_inside_cov=46	right_outside_cov=51
MC	41	.	NC_000913	257908	258683	768	0	left_inside_cov=0	left_outside_cov=100	right_inside_cov=0	right_outside_cov=100
MC	42	.	NC_000913	950364	954478	0	0	left_inside_cov=47	left_outside_cov=49	right_inside_cov=47	right_outside_cov=48
MC	43	.	NC_000913	1978503	1979278	767	0	left_inside_cov=0	left_outside_cov=103	right_inside_cov=0	right_outside_cov=103
MC	44	.	NC_000913	3423755	3424560	475	322	left_inside_cov=41	left_outside_cov=48	right_inside_cov=47	right_outside_cov=48
MC	45	.	NC_000913	3731119	3734617	0	0	left_inside_cov=12	left_outside_cov=54	right_inside_cov=47	right_outside_cov=48
MC	46	.	NC_000913	3933793	3937158	0	0	left_inside_cov=47	left_outside_cov=64	right_inside_cov=46	right_outside_cov=50
MC	47	.	NC_000913	3992385	3992392	0	0	left_inside_cov=0	left_outside_cov=133	right_inside_cov=0	right_outside_cov=133
MC	48	.	NC_000913	4144018	4147121	0	0	left_inside_cov=47	left_outside_cov=49	right_inside_cov=45	right_outside_cov=48
MC	49	.	NC_000913	4308514	4312027	0	0	left_inside_cov=43	left_outside_cov=50	right_inside_cov=43	right_outside_cov=49
JC	50	.	NC_000913	1	1	NC_000913	4641652	-1	0	alignment_overlap=0	circular_chromosome=1	coverage_minus=54	coverage_plus=52	flanking_left=139	flanking_right=139	frequency=1	junction_possible_overlap_registers=134	key=NC_000913__1__1__NC_000913__4641652__-1__0____139__139__0__0	max_left=138	max_left_minus=138	max_left_plus=135	max_min_left=68	max_min_left_minus=67	max_min_left_plus=68	max_min_right=66	max_min_right_minus=64	max_min_right_plus=66	max_pos_hash_score=270	max_right=137	max_right_minus=118	max_right_plus=137	neg_log10_pos_hash_p_value=0.5	new_junction_coverage=0.88	new_junction_read_count=106	polymorphism_frequency=1.000e+00	pos_hash_score=41	prediction=consensus	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.00	side_1_overlap=0	side_1_possible_overlap_registers=134	side_1_read_count=0	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.00	side_2_overlap=0	side_2_possible_overlap_registers=134	side_2_read_count=0	side_2_redundant=0	total_non_overlap_reads=106
JC	51	.	NC_000913	184853	1	NC_000913	3868063	1	0	alignment_overlap=0	coverage_minus=2	coverage_plus=1	flanking_left=139	flanking_right=139	frequency=2.817e-02	junction_possible_overlap_registers=134	key=NC_000913__184853__1__NC_000913__3868063__1__0____139__139__0__0	max_left=137	max_left_minus=137	max_left_plus=77	max_min_left=0	max_min_left_minus=0	max_min_left_plus=0	max_min_right=61	max_min_right_minus=39	max_min_right_plus=61	max_pos_hash_score=270	max_right=61	max_right_minus=39	max_right_plus=61	neg_log10_pos_hash_p_value=9.2	new_junction_coverage=0.03	new_junction_read_count=4	polymorphism_frequency=2.817e-02	pos_hash_score=3	prediction=polymorphism	reject=COVERAGE_EVENNESS_SKEW,FREQUENCY_CUTOFF	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=1.07	side_1_overlap=0	side_1_possible_overlap_registers=134	side_1_read_count=128	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=1.23	side_2_overlap=0	side_2_possible_overlap_registers=134	side_2_read_count=148	side_2_redundant=0	total_non_overlap_reads=3
JC	52	.	NC_000913	257907	-1	NC_000913	258684	1	0	alignment_overlap=8	coverage_minus=44	coverage_plus=48	flanking_left=139	flanking_right=139	frequency=1	junction_possible_overlap_registers=126	key=NC_000913__257907__-1__NC_000913__258676__1__8____139__139__0__0	max_left=127	max_left_minus=106	max_left_plus=127	max_min_left=64	max_min_left_minus=63	max_min_left_plus=64	max_min_right=62	max_min_right_minus=62	max_min_right_plus=60	max_pos_hash_score=254	max_right=129	max_right_minus=129	max_right_plus=128	neg_log10_pos_hash_p_value=0.5	new_junction_coverage=0.84	new_junction_read_count=95	polymorphism_frequency=1.000e+00	pos_hash_score=40	prediction=consensus	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.00	side_1_overlap=8	side_1_possible_overlap_registers=134	side_1_read_count=0	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.00	side_2_overlap=0	side_2_possible_overlap_registers=126	side_2_read_count=0	side_2_redundant=0	total_non_overlap_reads=92
JC	53	.	NC_000913	1207790	1	NC_000913	1209619	1	0	alignment_overlap=16	coverage_minus=36	coverage_plus=25	flanking_left=139	flanking_right=139	frequency=7.104e-01	junction_possible_overlap_registers=118	key=NC_000913__1207790__1__NC_000913__1209603__1__16____139__139__0__0	max_left=120	max_left_minus=120	max_left_plus=100	max_min_left=60	max_min_left_minus=47	max_min_left_plus=60	max_min_right=57	max_min_right_minus=57	max_min_right_plus=56	max_pos_hash_score=238	max_right=119	max_right_minus=119	max_right_plus=119	neg_log10_pos_hash_p_value=0.8	new_junction_coverage=0.58	new_junction_read_count=61	polymorphism_frequency=7.104e-01	pos_hash_score=32	prediction=polymorphism	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.16	side_1_overlap=16	side_1_possible_overlap_registers=134	side_1_read_count=19	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.31	side_2_overlap=0	side_2_possible_overlap_registers=118	side_2_read_count=33	side_2_redundant=0	total_non_overlap_reads=61
JC	54	.	NC_000913	1207805	-1	NC_000913	1209602	-1	0	alignment_overlap=16	coverage_minus=34	coverage_plus=38	flanking_left=139	flanking_right=139	frequency=7.433e-01	junction_possible_overlap_registers=118	key=NC_000913__1207805__-1__NC_000913__1209618__-1__16____139__139__0__0	max_left=122	max_left_minus=120	max_left_plus=122	max_min_left=58	max_min_left_minus=45	max_min_left_plus=58	max_min_right=60	max_min_right_minus=60	max_min_right_plus=57	max_pos_hash_score=238	max_right=120	max_right_minus=120	max_right_plus=112	neg_log10_pos_hash_p_value=0.9	new_junction_coverage=0.68	new_junction_read_count=72	polymorphism_frequency=7.433e-01	pos_hash_score=31	prediction=polymorphism	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.16	side_1_overlap=16	side_1_possible_overlap_registers=134	side_1_read_count=19	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.31	side_2_overlap=0	side_2_possible_overlap_registers=118	side_2_read_count=33	side_2_redundant=0	total_non_overlap_reads=72
JC	55	.	NC_000913	1299498	-1	NC_000913	1300698	1	0	alignment_overlap=4	coverage_minus=62	coverage_plus=49	flanking_left=139	flanking_right=139	frequency=1	junction_possible_overlap_registers=130	key=NC_000913__1299498__-1__NC_000913__1300694__1__4____139__139__0__0	max_left=130	max_left_minus=121	max_left_plus=130	max_min_left=66	max_min_left_minus=64	max_min_left_plus=66	max_min_right=63	max_min_right_minus=51	max_min_right_plus=63	max_pos_hash_score=262	max_right=132	max_right_minus=132	max_right_plus=121	neg_log10_pos_hash_p_value=0.3	new_junction_coverage=0.96	new_junction_read_count=112	polymorphism_frequency=1.000e+00	pos_hash_score=45	prediction=consensus	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.00	side_1_overlap=4	side_1_possible_overlap_registers=134	side_1_read_count=0	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.00	side_2_overlap=0	side_2_possible_overlap_registers=130	side_2_read_count=0	side_2_redundant=0	total_non_overlap_reads=111
JC	56	.	NC_000913	1467910	1	NC_000913	1653330	1	0	alignment_overlap=0	coverage_minus=2	coverage_plus=4	flanking_left=139	flanking_right=139	frequency=9.091e-02	junction_possible_overlap_registers=134	key=NC_000913__1467910__1__NC_000913__1653330__1__0____139__139__1__0	max_left=111	max_left_minus=111	max_left_plus=43	max_min_left=43	max_min_left_minus=43	max_min_left_plus=43	max_min_right=28	max_min_right_minus=28	max_min_right_plus=0	max_pos_hash_score=270	max_right=121	max_right_minus=58	max_right_plus=121	neg_log10_pos_hash_p_value=7.9	new_junction_coverage=0.07	new_junction_read_count=9	polymorphism_frequency=9.091e-02	pos_hash_score=5	prediction=polymorphism	reject=COVERAGE_EVENNESS_SKEW,FREQUENCY_CUTOFF	side_1_annotate_key=repeat	side_1_continuation=0	side_1_coverage=NA	side_1_overlap=0	side_1_read_count=NA	side_1_redundant=1	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.75	side_2_overlap=0	side_2_possible_overlap_registers=134	side_2_read_count=90	side_2_redundant=0	total_non_overlap_reads=6
JC	57	.	NC_000913	1469240	-1	NC_000913	1653334	-1	0	alignment_overlap=0	coverage_minus=2	coverage_plus=7	flanking_left=139	flanking_right=139	frequency=8.491e-02	junction_possible_overlap_registers=134	key=NC_000913__1469240__-1__NC_000913__1653334__-1__0____139__139__1__0	max_left=82	max_left_minus=63	max_left_plus=82	max_min_left=63	max_min_left_minus=63	max_min_left_plus=18	max_min_right=57	max_min_right_minus=0	max_min_right_plus=57	max_pos_hash_score=270	max_right=132	max_right_minus=106	max_right_plus=132	neg_log10_pos_hash_p_value=7.9	new_junction_coverage=0.07	new_junction_read_count=9	polymorphism_frequency=8.491e-02	pos_hash_score=5	prediction=polymorphism	reject=COVERAGE_EVENNESS_SKEW,FREQUENCY_CUTOFF	side_1_annotate_key=repeat	side_1_continuation=0	side_1_coverage=NA	side_1_overlap=0	side_1_read_count=NA	side_1_redundant=1	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.81	side_2_overlap=0	side_2_possible_overlap_registers=134	side_2_read_count=97	side_2_redundant=0	total_non_overlap_reads=9
JC	58	.	NC_000913	1978502	-1	NC_000913	1979279	1	0	alignment_overlap=8	coverage_minus=62	coverage_plus=36	flanking_left=139	flanking_right=139	frequency=1	junction_possible_overlap_registers=126	key=NC_000913__1978502__-1__NC_000913__1979271__1__8____139__139__0__0	max_left=130	max_left_minus=128	max_left_plus=130	max_min_left=64	max_min_left_minus=64	max_min_left_plus=38	max_min_right=65	max_min_right_minus=65	max_min_right_plus=53	max_pos_hash_score=254	max_right=129	max_right_minus=129	max_right_plus=124	neg_log10_pos_hash_p_value=0.5	new_junction_coverage=0.87	new_junction_read_count=98	polymorphism_frequency=1.000e+00	pos_hash_score=40	prediction=consensus	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.00	side_1_overlap=8	side_1_possible_overlap_registers=134	side_1_read_count=0	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.00	side_2_overlap=0	side_2_possible_overlap_registers=126	side_2_read_count=0	side_2_redundant=0	total_non_overlap_reads=98
JC	59	.	NC_000913	2514274	1	NC_000913	2536312	1	0	alignment_overlap=2	coverage_minus=49	coverage_plus=34	flanking_left=139	flanking_right=139	frequency=1	junction_possible_overlap_registers=132	key=NC_000913__2514274__1__NC_000913__2536310__1__2____139__139__1__0	max_left=135	max_left_minus=128	max_left_plus=135	max_min_left=65	max_min_left_minus=65	max_min_left_plus=61	max_min_right=66	max_min_right_minus=66	max_min_right_plus=66	max_pos_hash_score=266	max_right=129	max_right_minus=127	max_right_plus=129	neg_log10_pos_hash_p_value=0.7	new_junction_coverage=0.72	new_junction_read_count=85	polymorphism_frequency=1.000e+00	pos_hash_score=38	prediction=consensus	read_count_offset=6	side_1_annotate_key=repeat	side_1_continuation=0	side_1_coverage=NA	side_1_overlap=2	side_1_read_count=NA	side_1_redundant=1	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.00	side_2_overlap=0	side_2_possible_overlap_registers=126	side_2_read_count=0	side_2_redundant=0	total_non_overlap_reads=83
JC	60	.	NC_000913	2515616	-1	NC_000913	2536317	-1	0	alignment_overlap=3	coverage_minus=85	coverage_plus=47	flanking_left=139	flanking_right=139	frequency=1	junction_possible_overlap_registers=131	key=NC_000913__2515616__-1__NC_000913__2536320__-1__3____139__139__1__0	max_left=132	max_left_minus=132	max_left_plus=126	max_min_left=65	max_min_left_minus=63	max_min_left_plus=65	max_min_right=66	max_min_right_minus=64	max_min_right_plus=66	max_pos_hash_score=264	max_right=133	max_right_minus=133	max_right_plus=125	neg_log10_pos_hash_p_value=0.4	new_junction_coverage=1.12	new_junction_read_count=132	polymorphism_frequency=1.000e+00	pos_hash_score=42	prediction=consensus	read_count_offset=6	side_1_annotate_key=repeat	side_1_continuation=0	side_1_coverage=NA	side_1_overlap=3	side_1_read_count=NA	side_1_redundant=1	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.00	side_2_overlap=0	side_2_possible_overlap_registers=125	side_2_read_count=0	side_2_redundant=0	total_non_overlap_reads=132
JC	61	.	NC_000913	3992384	-1	NC_000913	3992393	1	0	alignment_overlap=1	coverage_minus=80	coverage_plus=52	flanking_left=139	flanking_right=139	frequency=1	junction_possible_overlap_registers=133	key=NC_000913__3992384__-1__NC_000913__3992392__1__1____139__139__0__0	max_left=129	max_left_minus=126	max_left_plus=129	max_min_left=68	max_min_left_minus=68	max_min_left_plus=68	max_min_right=68	max_min_right_minus=68	max_min_right_plus=61	max_pos_hash_score=268	max_right=134	max_right_minus=132	max_right_plus=134	neg_log10_pos_hash_p_value=0.1	new_junction_coverage=1.12	new_junction_read_count=133	polymorphism_frequency=1.000e+00	pos_hash_score=56	prediction=consensus	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.00	side_1_overlap=1	side_1_possible_overlap_registers=134	side_1_read_count=0	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.00	side_2_overlap=0	side_2_possible_overlap_registers=133	side_2_read_count=0	side_2_redundant=0	total_non_overlap_reads=132
JC	62	.	NC_000913	4542682	1	NC_000913	4542996	1	0	alignment_overlap=9	coverage_minus=2	coverage_plus=11	flanking_left=139	flanking_right=139	frequency=1.131e-01	junction_possible_overlap_registers=125	key=NC_000913__4542682__1__NC_000913__4542987__1__9____139__139__0__0	max_left=110	max_left_minus=2	max_left_plus=110	max_min_left=63	max_min_left_minus=2	max_min_left_plus=63	max_min_right=65	max_min_right_minus=0	max_min_right_plus=65	max_pos_hash_score=252	max_right=128	max_right_minus=128	max_right_plus=75	neg_log10_pos_hash_p_value=6.4	new_junction_coverage=0.12	new_junction_read_count=13	polymorphism_frequency=1.131e-01	pos_hash_score=7	prediction=polymorphism	reject=COVERAGE_EVENNESS_SKEW,FREQUENCY_CUTOFF	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.87	side_1_overlap=9	side_1_possible_overlap_registers=134	side_1_read_count=105	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.95	side_2_overlap=0	side_2_possible_overlap_registers=125	side_2_read_count=106	side_2_redundant=0	total_non_overlap_reads=13
JC	63	.	NC_000913	4542690	-1	NC_000913	4542986	-1	0	alignment_overlap=9	coverage_minus=1	coverage_plus=4	flanking_left=139	flanking_right=139	frequency=4.890e-02	junction_possible_overlap_registers=125	key=NC_000913__4542690__-1__NC_000913__4542995__-1__9____139__139__0__0	max_left=46	max_left_minus=6	max_left_plus=46	max_min_left=46	max_min_left_minus=6	max_min_left_plus=46	max_min_right=0	max_min_right_minus=0	max_min_right_plus=0	max_pos_hash_score=252	max_right=126	max_right_minus=124	max_right_plus=126	neg_log10_pos_hash_p_value=7.5	new_junction_coverage=0.04	new_junction_read_count=5	polymorphism_frequency=4.890e-02	pos_hash_score=5	prediction=polymorphism	reject=COVERAGE_EVENNESS_SKEW,FREQUENCY_CUTOFF	side_1_annotate_key=gene	side_1_continuation=0	side_1_coverage=0.81	side_1_overlap=9	side_1_possible_overlap_registers=134	side_1_read_count=97	side_1_redundant=0	side_2_annotate_key=gene	side_2_continuation=0	side_2_coverage=0.93	side_2_overlap=0	side_2_possible_overlap_registers=125	side_2_read_count=104	side_2_redundant=0	total_non_overlap_reads=5
UN	64	.	NC_000913	15516	16604
UN	65	.	NC_000913	19931	20433
UN	66	.	NC_000913	122998	127565
UN	67	.	NC_000913	223877	224651
UN	68	.	NC_000913	224655	224660
UN	69	.	NC_000913	225006	225454
UN	70	.	NC_000913	225852	225895
UN	71	.	NC_000913	226140	226169
UN	72	.	NC_000913	226429	226477
UN	73	.	NC_000913	226731	226839
UN	74	.	NC_000913	227122	228556
UN	75	.	NC_000913	228812	228874
UN	76	.	NC_000913	257908	258683
UN	77	.	NC_000913	270653	271165
UN	78	.	NC_000913	274088	275018
UN	79	.	NC_000913	279294	279812
UN	80	.	NC_000913	290767	291271
UN	81	.	NC_000913	315363	316349
UN	82	.	NC_000913	381385	382464
UN	83	.	NC_000913	391830	391830
UN	84	.	NC_000913	391832	391832
UN	85	.	NC_000913	391837	392838
UN	86	.	NC_000913	525996	526590
UN	87	.	NC_000913	566898	566898
UN	88	.	NC_000913	566905	567911
UN	89	.	NC_000913	574718	575673
UN	90	.	NC_000913	608136	609223
UN	91	.	NC_000913	687978	688933
UN	92	.	NC_000913	729930	730018
UN	93	.	NC_000913	732120	732159
UN	94	.	NC_000913	950396	954411
UN	95	.	NC_000913	1050175	1050271
UN	96	.	NC_000913	1094376	1095374
UN	97	.	NC_000913	1097444	1097444
UN	98	.	NC_000913	1097446	1097446
UN	99	.	NC_000913	1097448	1097454
UN	100	.	NC_000913	1299499	1300697
UN	101	.	NC_000913	1396150	1396150
UN	102	.	NC_000913	1396155	1397111
UN	103	.	NC_000913	1432403	1432524
UN	104	.	NC_000913	1432784	1433067
UN	105	.	NC_000913	1433071	1433071
UN	106	.	NC_000913	1433501	1433534
UN	107	.	NC_000913	1433786	1433947
UN	108	.	NC_000913	1433951	1433951
UN	109	.	NC_000913	1434206	1434223
UN	110	.	NC_000913	1468036	1469112
UN	111	.	NC_000913	1469114	1469114
UN	112	.	NC_000913	1469423	1470399
UN	113	.	NC_000913	1528450	1529050
UN	114	.	NC_000913	1571001	1571217
UN	115	.	NC_000913	1571521	1571671
UN	116	.	NC_000913	1633085	1633100
UN	117	.	NC_000913	1633349	1633510
UN	118	.	NC_000913	1633763	1633795
UN	119	.	NC_000913	1634220	1634514
UN	120	.	NC_000913	1634773	1634900
UN	121	.	NC_000913	1650972	1651419
UN	122	.	NC_000913	1978503	1979278
UN	123	.	NC_000913	2066309	2066338
UN	124	.	NC_000913	2066850	2067177
UN	125	.	NC_000913	2069067	2070147
UN	126	.	NC_000913	2101870	2102825
UN	127	.	NC_000913	2170300	2171305
UN	128	.	NC_000913	2289050	2289992
UN	129	.	NC_000913	2304681	2304681
UN	130	.	NC_000913	2304683	2304688
UN	131	.	NC_000913	2304690	2304692
UN	132	.	NC_000913	2304694	2304694
UN	133	.	NC_000913	2514402	2515490
UN	134	.	NC_000913	2726177	2729114
UN	135	.	NC_000913	2729686	2730821
UN	136	.	NC_000913	2731200	2731247
UN	137	.	NC_000913	2731252	2731253
UN	138	.	NC_000913	2996486	2997568
UN	139	.	NC_000913	3130264	3131213
UN	140	.	NC_000913	3186221	3187296
UN	141	.	NC_000913	3365683	3366627
UN	142	.	NC_000913	3423790	3424526
UN	143	.	NC_000913	3424783	3426714
UN	144	.	NC_000913	3426716	3426716
UN	145	.	NC_000913	3426946	3428427
UN	146	.	NC_000913	3428678	3428792
UN	147	.	NC_000913	3470296	3470609
UN	148	.	NC_000913	3470867	3470907
UN	149	.	NC_000913	3583550	3584068
UN	150	.	NC_000913	3619402	3620951
UN	151	.	NC_000913	3621210	3622168
UN	152	.	NC_000913	3652160	3653112
UN	153	.	NC_000913	3666534	3666752
UN	154	.	NC_000913	3667066	3667210
UN	155	.	NC_000913	3731142	3734592
UN	156	.	NC_000913	3762393	3763942
UN	157	.	NC_000913	3764210	3765154
UN	158	.	NC_000913	3933835	3937111
UN	159	.	NC_000913	3941779	3941886
UN	160	.	NC_000913	3942158	3943272
UN	161	.	NC_000913	3943519	3943551
UN	162	.	NC_000913	3943716	3943859
UN	163	.	NC_000913	3944187	3945439
UN	164	.	NC_000913	3945696	3945769
UN	165	.	NC_000913	3946043	3946096
UN	166	.	NC_000913	3946354	3946492
UN	167	.	NC_000913	3946820	3946820
UN	168	.	NC_000913	3992385	3992392
UN	169	.	NC_000913	4035289	4035612
UN	170	.	NC_000913	4035866	4036972
UN	171	.	NC_000913	4037220	4037347
UN	172	.	NC_000913	4037531	4037698
UN	173	.	NC_000913	4037968	4038563
UN	174	.	NC_000913	4038864	4039257
UN	175	.	NC_000913	4039525	4040477
UN	176	.	NC_000913	4144054	4147084
UN	177	.	NC_000913	4166417	4168089
UN	178	.	NC_000913	4168694	4171513
UN	179	.	NC_000913	4171516	4171517
UN	180	.	NC_000913	4176366	4176407
UN	181	.	NC_000913	4176412	4176412
UN	182	.	NC_000913	4176658	4176977
UN	183	.	NC_000913	4208253	4209598
UN	184	.	NC_000913	4209861	4209890
UN	185	.	NC_000913	4210153	4213040
UN	186	.	NC_000913	4296178	4296322
UN	187	.	NC_000913	4308543	4311987
UN	188	.	NC_000913	4498312	4499383
UN	189	.	NC_000913	4507585	4508558
