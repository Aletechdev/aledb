#!/usr/bin/python
"""
Implements a validatemutations() function and supporting functions to confirm the absence of dropout
mutations for a given ALE run. Assumes access to the database given by importation of
the alchemy_orm module.

Edit the BASEPATH constant as needed for the installation.

See documentation of the validatemutations function for more details.
    
NOTE: Currently this will only validate previously unvalidated mutations.
    Since it creates ObservedMutation entries to store the validations, these will
    show up as present in the mutation list and therefore not be counted
    as "dropout mutations".
    
    Having the getallmutations() function filter by the ObservedMutation.breseq_present
    field would change this behavior, although it would require adding an additional field
    to the alchemy_orm model for ResequencingExperiment 
"""
import os
import math, operator
import pysam
import alchemy_orm

BASEPATH = alchemy_orm.settings.sequencing_path

PHRED_ASCII_OFFSET=33 # value to subtract from the ASCII code of the quality character to get the Phred value.

def genotypelikelihood(reads,reference_base, m=1, g=1):
    u"""
    Computes the log likelihood that a set of reads comes from a genotype with a given number of matches to a reference at a single base.
    
    Adapted from:
    
    Eq. 2 in 
    
    Li, Heng. "A Statistical Framework for SNP Calling, Mutation Discovery, Association Mapping and Population Genetical Parameter Estimation from Sequencing Data." Bioinformatics 27, no. 21 (November 1, 2011): 2987-2993. doi:10.1093/bioinformatics/btr509.
     
    Uses a generalized negative binomial error model, taking into account the supplied Phred-scaled quality scores 
    for each read that give the estimated error probability at that base. This model assumes that errors
    are distributed independently of sequence composition (an assumption which does not hold for real sequences but is reasonable
    as a first approximation). However, if sequence dependence is accounted for by the software that generates the quality scores, 
    then this assumption is satisfied. This model also assumes that variation is biallelic.
    
    Input:
        reads: a list of dictionaries with attributes 'base' and 'phred'. The Phred score is assumed to be an integer in the form:
            phred = -10*log10(e) where e is the estimated probability of a base being incorrect.
        reference_base: the base in the reference genome at the mapped site
        
        (m): ploidy. This is 1 for bacterial chromosomes (but not for plasmids)
        (g): the likelihood returned is for a genome having this number of alleles matching the reference.
    
    Output:
        A log likelihood score: L(g)
        
        Such that:
        
            if:
        
            T is a genome matching the reference at g loci (out of m) for the given base
            
            and
            
            d is the set of sequencing reads observed,
            
            then
            
            L(g) = log10(Pr {d | T}) 
        
        In other words, L(g) represents the log likelihood of getting the given reads by sequencing a genome that matches the reference at exactly g of m possible loci.
        
        For haploid organisms where m=1 there are only two cases:
            If g=1 then L(g) is the log likelihood of getting the given reads by sequencing a genome that matches the reference at this base.
            If g=0 then L(g) is the log likelihood of getting the given reads by sequencing a genome that doesn't matches the reference at this base
                (i.e. is from a mutant).
                
        Note that this is not the same as the posterior probability, Pr {T | d}, which would be the probability that the 
        true genome has g matches at m loci given the reads d.
    """
    # define a product function
    def prod(factors):
        return reduce(operator.mul, factors, 1)
    
    # define a pair of functions to convert to and from Phred scale
    def dePhred(phred_score):
        return 10**(float(phred_score)/-10)
    
    def rePhred(likelihood):
        return -10*math.log10(likelihood)
      
    reference_reads=[]
    mismatch_reads=[]
    
    # segregate the reads into two lists: matching (reference) and not (mis_match)
    for read in reads:
        if read['base'].upper()==reference_base.upper():
            reference_reads.append(read)
        else:
            mismatch_reads.append(read)
              
    k = len(reads)
    l = len(reference_reads)
    
    if l > 0: #
        ref_product = prod([(m - g) * dePhred(ref_read['phred']) + g * (1 - dePhred(ref_read['phred'])) for ref_read in reference_reads])
    else:
        ref_product = 1
        
    mismatch_product = prod([(m - g) * (1 - dePhred(mut_read['phred'])) + g * dePhred(mut_read['phred']) for mut_read in mismatch_reads])
    
    if ref_product == 0: # if we've underflowed this product, the probability is too low to consider, call it -inf 
        return float('-inf')
    else:
        return math.log10((1/float(m)**k) * ref_product * mismatch_product)


def getreads(bamfile, reference, position):
    """
    Uses pysam to determine the identity of bases in aligned reads at a given position (0-based).
    
    Input:
        bamfile      a path to a valid bam file containing the alignment
        reference    the name of the sequence reference in the bam file
        position     the position to examine (0-based)
        
    Returns: 
        reads        a list of dictionaries, one for each read.
            qname    the name of the read
            base     the base at the given position in the read
            phred    phred quality score (in numeric format)
    """
    samfile=pysam.Samfile(bamfile,'rb')

    reads=[]
    for pileupcolumn in samfile.pileup(reference,position,position+1):
        if pileupcolumn.pos==position:
            for pileupread in pileupcolumn.pileups:
                new_read={'qname':pileupread.alignment.qname,'base':pileupread.alignment.seq[pileupread.qpos], 'phred':ord(pileupread.alignment.qual[pileupread.qpos])-PHRED_ASCII_OFFSET,}
                reads.append(new_read)
    return reads

def getrefbase(fasta_file,reference,position):
    """
    Wrapper function that uses pysam to read the base at a given position (0-based) in a fasta file.
    """
    return pysam.Fastafile(fasta_file).fetch(reference,position,position+1)

def annotatemutation(session, dropout_mutation_id, sequencing_experiment, data_location, verbose=False):
    """
    Given the IDs of a mutation and a sequencing experiment, whether or not the mutation
    is called by breseq, and the path to a breseq data folder,
    create or update the following fields on an ObservedMutation:
        
        present
        wt_reads
        mutated_reads
        other_reads
    
    Note: currently only defined for SNP mutations.
    """
    defined_mutation_types=['SNP']
    
    observed_mutation = alchemy_orm.query_or_create(session,alchemy_orm.ObservedMutation,mutation_id=dropout_mutation_id,sequencing_experiment_id=sequencing_experiment)
    
    # get the information on the mutation it's associated with (can't get this to work through the ORM)
    mutation=session.query(alchemy_orm.Mutation).filter_by(id=dropout_mutation_id).one()

    print "Validating mutation id {} in resequencing experiment {}".format(dropout_mutation_id, sequencing_experiment)
    
    if mutation.mutation_type in defined_mutation_types:
        print "mutation type: {}".format(mutation.mutation_type)
        # figure out what the mutated base is (parse from end of text field):
        mut_base=mutation.sequence_change[-1]
        ref_base=getrefbase(os.path.join(data_location,'data/reference.fasta'),'NC_000913',mutation.position - 1 ) # subtract 1 to go from 1-based sequence position to 0-based pysam position
        
        reads=getreads(os.path.join(data_location,'data/reference.bam'),'NC_000913',mutation.position - 1 ) # subtract 1 to go from 1-based sequence position to 0-based pysam position
        
        mut_count=0
        ref_count=0
        other_count=0
        for read in reads:
            if read['base']==mut_base:
                mut_count+=1
            if read['base']==ref_base:
                ref_count+=1
            if read['base']!=mut_base and read['base']!=ref_base:
                other_count+=1
                
        observed_mutation.wt_reads=ref_count
        observed_mutation.mutated_reads=mut_count
        observed_mutation.other_reads=other_count
        if observed_mutation.breseq_present is None:
            observed_mutation.breseq_present = False

        gl_wt = genotypelikelihood(reads,ref_base,m=1,g=1)
        gl_mut = genotypelikelihood(reads,ref_base,m=1,g=0)
        
        observed_mutation.reference_genome_likelihood = gl_wt
                
        if gl_mut > gl_wt:
            observed_mutation.present=True
        else:
            observed_mutation.present=False
        
        session.add(observed_mutation)
        
        if verbose:
            print "reference base = %s, mutation base = %s" % (ref_base, mut_base)
            print "%d reads support the reference" % (ref_count)
            print "%d reads support the mutation" % (mut_count)
            print "%d support neither" % (other_count)
            print "likelihood of reads = {} for genome matching reference, {} for genome not matching reference".format(gl_wt, gl_mut)
            print "mutation present? {}".format(str(observed_mutation.present).upper())
            print 
    else:
        if verbose:
            print "validation currently not implemented for mutation type {}, skipping".format(mutation.mutation_type)
        
 
def getallmutations(experiment_id,ale_number):
    """
    Given an experiment and ale number, return a dictionary of all observed mutations for that ale, keyed by flask number, then
    by isolate number.
    """
    mutation_validation_session=alchemy_orm.Session()
    
    all_reseqs=mutation_validation_session.query(alchemy_orm.ResequencingExperiment).\
        join(alchemy_orm.Isolate, alchemy_orm.ResequencingExperiment.isolate_id == alchemy_orm.Isolate.id).\
        join(alchemy_orm.Flask, alchemy_orm.Isolate.flask_id == alchemy_orm.Flask.id).\
        join(alchemy_orm.AleId, alchemy_orm.Flask.ale_id_id == alchemy_orm.AleId.id).\
        join(alchemy_orm.AleExperiment, alchemy_orm.AleId.ale_experiment_id == alchemy_orm.AleExperiment.ale_id).\
        filter(alchemy_orm.AleId.ale_id == ale_number, alchemy_orm.AleExperiment.ale_id == experiment_id)
        
    all_mutations={}
    
    # construct a nested dictionary from the mutations    
    for reseq in all_reseqs:
        if reseq.isolate.flask.flask_number not in all_mutations:
            all_mutations[reseq.isolate.flask.flask_number]={}
        if reseq.isolate.isolate_number in all_mutations[reseq.isolate.flask.flask_number]:
            raise Exception("Duplicate sequencing run! A sequencing experiment already exists for Experiment {}, Ale {}, Flask {}, Isolate {} already exists".format(experiment_id,ale_number,reseq.isolate.flask.flask_number,reseq.isolate.isolate_number))
        else:
            all_mutations[reseq.isolate.flask.flask_number][reseq.isolate.isolate_number]=[mut.id for mut in reseq.mutations]  # TODO exclude not present mutations 
    return all_mutations

                
def finddropoutmutations(all_mutations):
    """
    Find the mutations that have dropped out of an ALE lineage.
    
    A dropout mutation is defined as one that appears in all isolates of the previous flask in a lineage but is
    not present in any isolate of the current flask.
    
    Input:
        all_mutations: A dictionary of all the mutation IDs in a particular ALE lineage, keyed by flask number, then
            isolate number
        
    Output:
        A dictionary of IDs of dropout mutations, keyed by flask number. 
    """
    # create a dictionary of mutations that have disappeared in all_mutations
    dropout_mutations={}
    # make a list of every flask for this ale sorted in chronological order 
    flask_list=sorted(all_mutations.keys())
    if len(flask_list)>1: # dropout mutations can only exist with more than one flask
        # Idea: create two lists that will parallel the flask list,
        # one for mutation ids found in every isolate of the corresponding flask (intersection of isolates)
        # and one for mutation ids found in any isolate of the corresponding flask (union of isolates)
        # then we compare the intersection to the union.
        intersect_flask_mutations=[]
        union_flask_mutations=[]
        for flask_index,flask_number in enumerate(flask_list):
            # create a list of sets of mutation ids for each isolate of this flask
            isolate_mutations=[]
            for isolate_number in all_mutations[flask_number]:
                isolate_mutations.append(set([mut for mut in all_mutations[flask_number][isolate_number]]))
            intersect_flask_mutations.append(set.intersection(*isolate_mutations))
            union_flask_mutations.append(set.union(*isolate_mutations))
            # Find any mutations that appear in all the isolates of the previous flask
            # but none of the isolates in the current flask (they've dropped out)
            # then store the dropout mutations in a dictionary keyed by flask number
            if flask_index >= 1:
                dropout_mutations[flask_number]=intersect_flask_mutations[flask_index-1]-union_flask_mutations[flask_index]
    return dropout_mutations


def check_negative_predictions(experiment_id,ale_number):
    """
    Given the id of an experiment and ALE number, finds all dropout mutations (negative predictions)
    and checks the reads aligning to the mutation position. Based on the genome
    likelihood values, each mutation is called as either present or not present
    an an ObservedMutation record created in the database to store the 
    validation annotation.
    """
    # generate a dictionary of all mutation_ids for all runs
    all_mutations=getallmutations(experiment_id,ale_number)
    # figure out which ones were present and then drop out
    dropout_mutations=finddropoutmutations(all_mutations)
  
    validation_session=alchemy_orm.Session()

    # iterate through each dropout mutation in each flask
    for flask_number in dropout_mutations:
        for dropout_mutation_id in dropout_mutations[flask_number]:
            print "Validating dropout mutation id {}".format(dropout_mutation_id)
            
            for isolate_number in all_mutations[flask_number]: # do this for each isolate
                print "in isolate {}".format(isolate_number) 
                seq_exp=validation_session.query(alchemy_orm.ResequencingExperiment).join(alchemy_orm.Isolate, alchemy_orm.ResequencingExperiment.isolate_id == alchemy_orm.Isolate.id).\
                    join(alchemy_orm.Flask, alchemy_orm.Isolate.flask_id == alchemy_orm.Flask.id).\
                    join(alchemy_orm.AleId, alchemy_orm.Flask.ale_id_id == alchemy_orm.AleId.id).\
                    join(alchemy_orm.AleExperiment, alchemy_orm.AleId.ale_experiment_id == alchemy_orm.AleExperiment.ale_id).\
                    filter(alchemy_orm.AleExperiment.ale_id == experiment_id,
                           alchemy_orm.Flask.flask_number == flask_number,
                           alchemy_orm.Isolate.isolate_number == isolate_number).one()


                # get the path to the breseq data:
                datapath=os.path.join(BASEPATH,seq_exp.location)

                # annotate the mutation
                annotatemutation(validation_session,dropout_mutation_id, seq_exp.id, datapath)
    # commit the changes
    validation_session.commit()
                
