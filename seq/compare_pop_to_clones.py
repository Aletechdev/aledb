from models import *
from collections import Counter
import xlwt
from xlwt import Workbook,Style

def compare_mutation_calls(experiment_id,ale_no):
    reseqs = ResequencingExperiment.objects.raw("""SELECT reseq_id 
                   AS id FROM id_mapping WHERE experiment_id=%d AND 
                   ale_no=%d AND reseq_id IS NOT NULL ORDER BY flask_no
                   ,isolate_no ASC""" % (experiment_id,ale_no))
                                     
    clones = [r for r in reseqs if r.isolate.__unicode__().find("POP")==-1]
    pops = dict((r.flask_number,r) for r in reseqs if r.isolate.__unicode__().find("POP")>-1)

    pop_oms = dict((i,ObservedMutation.objects.filter(sequencing_experiment_id=pops.get(i).id)) for i in pops.keys())
    clone_map = dict((i.flask_number,list()) for i in clones)
    for r in clones:
        clone_map.get(r.flask_number).append(r)
    clone_oms = dict((f,ObservedMutation.objects.filter(sequencing_experiment_id__in=[r.id for r in clone_map.get(f)])) for f in clone_map.keys())
    
    print "----------Population calls----------\n"
    for i in sorted(pop_oms.keys()):
        print "Flask %s: \n" % i
        oms = pop_oms.get(i)
        calls = dict((om,float(om.frequency.replace("%",""))) for om in oms)
        for c in calls:
            if calls.get(c) > 60.0:        
                print "%s %s\n" % (c.mutation.__str__(),c.frequency)
    print "----------Clone calls----------\n"
    for i in sorted(pop_oms.keys()):
        print "Flask %s: \n" % i
        oms = clone_oms.get(i)
        mutations = [o.mutation for o in oms]
        mutation_spectrum = Counter(mutations)
        for i in mutation_spectrum:
            if mutation_spectrum.get(i)>1:
                print "%s\n" % i.__str__()
  
    """
    # List variants called by clone and pop reseqs and write to spreadsheet
    output = xlwt.Workbook()
    for i in sorted(pop_oms.keys()):
        sh = output.add_sheet("FLASK %d" % (i))
        sh.write(0,0,"Clone Mutations")
        sh.write(0,1,"# Observed")
        sh.write(0,2,"Pop Mutations")
        sh.write(0,3,"Frequency")

        pop_observed = pop_oms.get(i)
        pop_calls = dict((om.mutation,float(om.frequency.replace("%",""))) for om in pop_observed)

        clone_observed = clone_oms.get(i)
        clone_mutations = [o.mutation for o in clone_observed]
        mutation_spectrum = Counter(clone_mutations)
        
        for j,m in enumerate(sorted(mutation_spectrum,key = lambda mutation:mutation_spectrum.get(mutation),reverse=True)):
            sh.write(j+1,0,m.__str__())
            sh.write(j+1,1,"%d/%d" % (mutation_spectrum.get(m),len(clone_map.get(i))))
            sh.write(j+1,3,pop_calls.get(m))
    output.save("ale%d_analysis.xls" % ale_no)
    
        for j,m in enumerate(sorted(mutation_spectrum,key=lambda mutation: mutation.position)):
            if m.reference_error:
                sh.write(j+1,0,m.__str__(),Style.easyxf('pattern: pattern solid, fore_colour red;'))
            else:
                sh.write(j+1,0,m.__str__())
                sh.write(j+1,1,"%d/%d" % (mutation_spectrum.get(m),len(clone_map.get(i))))
  
n	Gene	Protein change	A7 F55 I5	A7 F55 I6	A7 F55 I7	A7 F55 I8	A7 F55 I9	A7 F55 I10	A7 F61 I1	A7 F88 I1	A7 F88 I2	A7 F88 I3	A7 F236 I1	A7 F422 I1	A7 F20 I1	A7 F20 I2	A7 F20 I3	A7 F55 I1	A7 F55 I2	A7 F55 I3	A7 F55 I4
4181279 T→C	rpoB	L671P (CTG→CCG) 							RA	0/210	0/161	1/118	0/141								
4181281 G→A	rpoB	E672K (GAA→AAA) 	RA	RA	RA	RA	RA	RA		RA	RA	RA	0/142	0/121				RA		RA	
4182601 A→C	rpoB	M1112L (ATC→CTC) 																	RA		
4184626 A→C	rpoC	E418D (GAA→GAC) 											RA	RA							
4185547 G→A	rpoC	M725I (ATG→ATA) 																			RA
        j = 1
        for c in sorted(pop_calls,key=lambda observed: observed.mutation.position):
            if pop_calls.get(c) > 90:
                if c.mutation.reference_error:
                    sh.write(j,2,c.mutation.__str__(),Style.easyxf('pattern: pattern solid, fore_colour red;'))
                else:
                    sh.write(j,2,c.mutation.__str__())
                sh.write(j,3,c.frequency)    
                j = j + 1

    output.save("ale%d_analysis.xls" % ale_no)
    """   
    
    # Track fixed/frequent variants across flasks
    output = xlwt.Workbook()
    sh = output.add_sheet("track")
    for j,flask in enumerate(sorted(pop_oms)):
        sh.write(0,j,"Flask %d" % flask)
        print "-------Flask %d-------" % flask
        pop_observed = pop_oms.get(flask)
        i = 1
        for observed in sorted(pop_observed,key=lambda observed: observed.mutation.position):
            if not observed.mutation.reference_error and float(observed.frequency.replace("%","")) > 60:
                print observed.mutation.__str__()
                sh.write(i,j,observed.mutation.__str__())
                i+=1
    output.save("ale%d_track.xls" % ale_no)
    
