#! /usr/bin/env python3
#Virathon: Genomic Analysis of Viruses of Archaea and Bacteria
from collections import defaultdict
from Bio import SeqIO
from Bio import SearchIO
from Bio.SeqUtils import gc_fraction
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import argparse
import subprocess
import re
import glob
import gzip
import os

parser = argparse.ArgumentParser()
parser.add_argument("--genome_files", help="File of genomic sequences", type =str, nargs="+")
parser.add_argument("--cds_files", help="File of CDS protein sequences", type =str, nargs="+")
parser.add_argument("--gene_files", help="File of CDS DNA sequences", type =str, nargs="+")
parser.add_argument("--in_format", help="Input Sequence file format", default="fasta", type =str)
parser.add_argument("--info_output", help="The output table file with the generated data for the genomic sequences", default="Seq_Info.tsv", type =str)
parser.add_argument("--rename_seqs", help="Flag to rename genomic sequences while indexing. CDS and Gene sequence files cannot be renamed.", default=False, type=bool)
parser.add_argument("--string_rename", help="String to use when renaming genomics sequences", default='Seq_', type=str)
parser.add_argument("--min_length", help="Minimum genomic sequence length", default=0, type=int)
parser.add_argument("--max_length", help="Maximum genomic sequence length", default=3000000, type=int)
parser.add_argument("--out_seq_file", help="Name of the merged output file of genome sequences", default='Merged_Sequences.fasta', type=str)
parser.add_argument("--call_prodigal_module", help="Flag to run the gene calling module", default=False, type=bool)
parser.add_argument("--bacphlip", help="Flag to run the Bacphlip", default=False, type=bool)
parser.add_argument("--call_vibrant_module", help="Flag to run the VIBRANT module", default=False, type=bool)
parser.add_argument("--call_checkv_module", help="Flag to run the CheckV module", default=False, type=bool)
parser.add_argument("--call_vhmnet_module", help="Flag to run the VirHostMatcher-Net module", default=False, type=bool)
parser.add_argument("--call_virsorter2_module", help="Flag to run the VirSorter2 module", default=False, type=bool)
parser.add_argument("--vhmnet_mode_short", help="Flag to run the VirHostMatcher-Net using the --short-contig flag", default=False, type=bool)
parser.add_argument("--phist_host_prediction", help="Flag to run the PHIST module for host prediction", default=False, type=bool)
parser.add_argument("--putative_host_genomes_directory", help="Directory containing fasta files of putative host genomes to be used by the PHIST module for host prediction", type=str)
parser.add_argument("--extension_putative_host_genomes", help="Extension of the fasta files in the directory containing putative host genomes", type=str, default="fasta")
parser.add_argument("--remove_exact_matches", help="Flag to remove exact matches with viral sequences from putative host genomes before running PHIST. Useful for when hostgs might be contaminaded with viral sequences or contain prophages", default=False, type=bool)
parser.add_argument("--call_rafah", help="Flag to run the RaFAH module for host prediction", default=False, type=bool)
parser.add_argument("--call_vpf_class", help="Flag to run the VPF-class module for taxonomic assingment and host prediction", default=False, type=bool)
parser.add_argument("--vpf_class_yaml", help=".yaml file necessary to run vpf_class",  default='/mnt/lustre/bio/users/fcoutinho/VPF_Class_Files/data-index.yaml', type=str)
parser.add_argument("--rafah_min_score", help="Minimum RaFAH score to consider a prediction as valid", default=0, type=float)
parser.add_argument("--metabat2", help="Flag to perform sequence binning through Metabat2", default=False, type=bool)
parser.add_argument("--make_pops_module", help="Flag to run the viral population pipeline", default=False, type=bool)
parser.add_argument("--make_plots_module", help="Flag to run the Plotting module based on the collected Seq Info", default=False, type=bool)
parser.add_argument("--pairwise_protein_scores", help="Flag to run the Paiwise Protein Scores (PPS) module", default=False, type=bool)
parser.add_argument("--pps_subject_fasta", help="Fasta file containing the subject protein sequences to be used by the PPS module", default='NA', type=str)
parser.add_argument("--pps_subject_db", help="MMSeqs fomated Database file containing the subject protein sequences to be used by the PPS module", default='NA', type=str)
parser.add_argument("--pps_min_aai", help="Minimum AAI to report in the PPS table", default=30, type=float)
parser.add_argument("--pps_min_perc_matched", help="Minimum percentage of matched CDS to report in the PPS table", default=30, type=float)
parser.add_argument("--pps_min_matched", help="Minimum number of matched CDS to report in the PPS table", default=3, type=int)
parser.add_argument("--pps_hits_table", help="Optional m8 table generated by MMSeqs2. When provided the search steps are skipped and the provided table is used as input to calculate pairwise protein scores instead", default='NA', type=str)
parser.add_argument("--call_ogtable_module", help="Flag to run the Orthologous Group table generation module", default=False, type=bool)
parser.add_argument("--call_ogscoretable_module", help="Flag to run the Orthologous Group Score table generation module", default=False, type=bool)
parser.add_argument("--og_phylogeny", help="Flag to run the Orthologous Group phylogeny reconstruction", default=False, type=bool)
parser.add_argument("--call_hmmer", help="Flag to query the CDS file against a hmmer database", default=False, type=bool)
parser.add_argument("--hmmer_db", help="Hmmer DB file prefix", default=False, type=str)
parser.add_argument("--hmmer_program", help="Hmmer program to run (hmmscan or hmmsearch)", default='hmmsearch', type=str)
parser.add_argument("--hmmer_min_score", help="Minimum Hmmer score to consider a match as valid", default=50, type=float)
parser.add_argument("--hmmer_max_evalue", help="Maximum Hmmer -evalue to consider a match as valid", default=0.001, type=float)
#Bowtie2 Abundance options
parser.add_argument("--abundance_table", help="Flag to run the abundance calculation modules", default=False, type=bool)
parser.add_argument("--abundance_rpkm", help="Flag to calculate abundance as RPKM", default=False, type=bool)
parser.add_argument("--abundance_max_reads", help="Set a maximum number of reads per sample to be mapped by parsed by bowtie2. All other reads are ignored. Default behavior is to use all reads in the sample", default=0, type=int)
parser.add_argument("--abundance_min_count", help="Set a minimum number of reads mapped to a sequence to consider include it in the abundance tables. Default behavior is to use all counts above 0", default=0, type=int)
parser.add_argument("--bowtiedb", help="Prefix of Bowtie DB to use for abundance calculations instead of building from the genomes file", default='NA', type=str)
parser.add_argument("--bowtie_mode", help="Alignment mode to run bowtie", default='sensitive', type=str)
parser.add_argument("--bowtie_k", help="Value for the Bowtie2 -k parameter. If not specified will use default mode, i.e. look for all alignments and only report the best one(s)", default=0, type=int)
parser.add_argument("--raw_read_table", help=".tsv file specifying the Sample ID, R1 Reads file, R2 Reads File, and Sample Group", type=str)
#Abundance options to be deprecated:
parser.add_argument("--metagenomes_dir", help="Directories containing metagenome fastq files to be used for abundance calculation",  nargs="+", type=str)
#SPAdes assembly options:
parser.add_argument("--metagenomes_extension", help="Extension of the fastq files in metagenomes_dir to be used for abundance calculation", default="fastq", type=str)
parser.add_argument("--assemble", help="Flag to run the assembly module", default=False, type=bool)
parser.add_argument("--min_cluster_size", help="The minimum number of proteins in a cluster to be used by the ogscoretable_module and ogphylogeny modules", default=3, type=int)
parser.add_argument("--threads", help="The number of threads to be used", default=1, type=int)
parser.add_argument("--max_ram", help="The maxmimum RAM to be used during analysis", default=1, type=int)
parser.add_argument("--parse_only", help="Flag to skip running any programs and only parse their output using selected parameters", default=False, type=bool)
args = parser.parse_args()


#This is the main function that calls all the other functions according to the user specified parameters
def central():
    #Run the assembly module if specified by the user
    if (args.assemble == True):
        if ((args.genome_files) or (args.cds_files) or (args.gene_files)):
            print(f"WARNING! The sequences generated by the assembly will be used and any genome, cds, or gene files provided will be ignored.")  
        args.genome_files = call_spades(raw_read_table=args.raw_read_table,spades_memory=args.max_ram)
        #Scaffold generated by SPAdes must always be renamed
        args.rename_seqs =True
    #Run the index module for the genomic sequences, if provided
    if (args.genome_files):
        index_seqs(in_seq_files=args.genome_files,rename_seqs=args.rename_seqs, seq_type="genomic", out_seq_file=merged_genomes_file)
        print(f"Merged genomic seqs file: {merged_genomes_file}")
    #Perform gene calling with prodigal through the call_prodigal function if specified by the user
    if (args.call_prodigal_module == True):
        (out_cds_file,out_genes_file,gff_file) = call_prodigal(merged_genomes_file)
        print('Generated files:',merged_cds_file,merged_genes_file,gff_file)
        #Index gene and cds files generated by prodigal
        index_seqs(in_seq_files=merged_genes_file,rename_seqs=False, seq_type="gene")
        index_seqs(in_seq_files=args.cds_files,rename_seqs=False, seq_type="cds")
    #Index gene and cds files supplid by the user, only when prodigal generated files have not been generated.
    else:
        if (args.gene_files):
            index_seqs(in_seq_files=args.gene_files,rename_seqs=False, seq_type="gene", out_seq_file=merged_genes_file)
            print(f"Merged genes file: {merged_genes_file}")
        if (args.cds_files):
            index_seqs(in_seq_files=args.cds_files,rename_seqs=False, seq_type="cds", out_seq_file=merged_cds_file)
            print(f"Merged CDS file: {merged_cds_file}")      
    #Cluster sequences into viral populations if specified by the user
    vpop_out_file = 'NA'
    if (args.make_pops_module):
        vpop_out_file = make_pops(merged_genomes_file,args.gene)
    #If specified by the user perform virus prediction with VIBRANT and Index the results
    bacphlip_out_file = 'NA'
    if (args.bacphlip == True):
        (bacphlip_out_file) = call_bacphlip(merged_genomes_file)
    #If specified by the user perform virus prediction with VirSorter2 and Index the results
    virsorter_outfile = 'NA'
    if (args.call_virsorter2_module == True):
        (virsorter_outfile) = call_virsorter2(merged_genomes_file)
    #If specified by the user perform virus prediction with VIBRANT and Index the results
    vibrant_out_quality_file = 'NA'
    vibrant_out_amg_file = 'NA'
    if (args.call_vibrant_module == True):
        (vibrant_out_quality_file,vibrant_out_amg_file) = call_vibrant(merged_genomes_file)
    #If specified by the user perform virus genome QC with CheckV and Index the results
    checkv_out_summary_file = 'NA'
    if (args.call_checkv_module == True):
        checkv_out_summary_file = call_checkv(merged_genomes_file)
    rafah_out_file = 'NA'
    if (args.call_rafah == True):
        rafah_out_file = call_rafah(merged_genomes_file,args.cds,args.rafah_min_score)
    phist_out_file = 'NA'
    if (args.phist_host_prediction == True):
        phist_out_file = call_phist(genome_file=merged_genomes_file,putative_host_genomes_directory=args.putative_host_genomes_directory,extension_putative_host_genomes=args.extension_putative_host_genomes,remove_exact_matches=args.remove_exact_matches)
    #If specified by the user perform virus host prediction through VirHostMatcher-Net and Index the results
    vhmnet_out_dir = 'NA'
    if (args.call_vhmnet_module == True):
        vhmnet_out_dir = call_vhmnet(merged_genomes_file)
    #If specificed by the user (args.hmmer == True) run the hmmer module
    if (args.call_hmmer == True):
        hmmer_search_outfile = call_hmmer(args.cds,args.hmmer_db,args.hmmer_program)
        (genome_hmm_scores,pairwise_scores) = parse_hmmer_output(hmmer_search_outfile,args.hmmer_max_evalue,args.hmmer_min_score)
        #Print pairwise_scores to og_score_table_out_file
        pairwise_score_table_out_file = 'OG_Pairwise_Score_Table_'+hmmer_search_outfile+'.tsv'
        pairwise_score_table_data_frame = pd.DataFrame.from_dict(pairwise_scores)
        print(f'Printing OG x CDS pairwise scores table to {pairwise_score_table_out_file}')
        pairwise_score_table_data_frame.to_csv(pairwise_score_table_out_file,sep="\t",na_rep='NA')
    #If specified by the user perform clustering of proteins into OGs and Index the results
    og_table_out_file = 'NA'
    if (args.call_ogtable_module == True):
        (og_table_out_file) = make_og_table(merged_genomes_file,args.cds)
    #If specified by the user perform clustering of proteins into OGs, align OGs, convert to HMMs map CDS back to OGs with hmmscan and Index the results
    og_score_table_out_file = 'NA'
    if ((args.call_ogscoretable_module == True) or (args.og_phylogeny == True)):
        og_score_table_out_file = make_og_score_table_and_phylogeny(merged_genomes_file,args.cds,args.min_cluster_size,args.call_ogscoretable_module,args.og_phylogeny)
    #If specified by the user perform binning  through Metabat2 and Index the results
    metabat_out_file = 'NA'
    if (args.metabat2 == True):
        metabat_out_file = call_metabat(merged_genomes_file)
        #If specified by the user perform binning  through Metabat2 and Index the results
    abundance_out_file = 'NA'
    if (args.abundance_table == True):
        abundance_out_file = calc_abundance(merged_genomes_file,args.bowtiedb,args.metagenomes_dir,args.metagenomes_extension,args.abundance_max_reads,args.bowtie_mode,args.abundance_min_count,args.raw_read_table)
    if (args.pairwise_protein_scores == True):
        calc_pps(merged_genomes_file,args.cds,args.pps_subject_fasta,args.pps_subject_db,args.pps_hits_table)
    if (args.call_vpf_class == True):
        vpf_class_outfile = call_vpf_class(merged_genomes_file,args.vpf_class_yaml)
    #Always print the results collected in seq_info
    print_results(seq_info,og_table_out_file,og_score_table_out_file,vibrant_out_quality_file,vibrant_out_amg_file,checkv_out_summary_file,vhmnet_out_dir,args.info_output,merged_genomes_file,metabat_out_file,rafah_out_file)

def index_seqs(in_seq_files=[],seq_type=None,rename_seqs=False,out_seq_file=None):
    print("Running indexing module")
    seq_counter = 0
    filtered_seqs = 0
    seen_ids= dict()
    if (out_seq_file):
        OUT = open(out_seq_file,'w', newline='')
    #with open(out_seq_file, 'w', newline='') as OUT:
    for seq_file in in_seq_files:
        print ("Indexing sequences from",seq_file)
        #Iterate over sequences in the file. Collect basic Info
        for seqobj in SeqIO.parse(seq_file, args.in_format):
            seq_passed = True
            seq_counter += 1
            if (seq_counter % 100000 == 0):
                print(f"\tProcessed {seq_counter} sequences")
            #Record description, length,  file source, and GC for genomic sequences only
            if (seq_type == 'genomic'):
                #Rename genomic sequences if specified by the user
                if (rename_seqs == True):
                    new_id = args.string_rename+str(seq_counter)
                    seq_info['Original_ID'][new_id] = seqobj.id
                    seqobj.id = new_id
                #Skip genomic sequences outside the length range   
                seq_length = len(seqobj.seq)
                if ((seq_length >= args.min_length) and (seq_length <= args.max_length)):
                    seq_info['Description'][seqobj.id] = seqobj.description
                    seq_info['GC'][seqobj.id] = round(gc_fraction(seqobj.seq),2)
                    seq_info['Length'][seqobj.id] = seq_length
                    seq_info['Original_File'][seqobj.id] = seq_file
                else:
                    filtered_seqs += 1
                    seq_passed == False
            elif (seq_type == 'cds'):
                [scaffold_id,cds_num] = seqobj.id.rsplit('_',1)
                if (scaffold_id not in seq_info['CDS_Count']):
                    seq_info['CDS_Count'][scaffold_id] = 0
                #Increment cds count of the scaffold
                seq_info['CDS_Count'][scaffold_id] += 1
            elif (seq_type == 'gene'):
                [scaffold_id,cds_num] = seqobj.id.rsplit('_',1)
                if (scaffold_id not in seq_info['Gene_Count']):
                    seq_info['Gene_Count'][scaffold_id] = 0
                #Increment gene count of the scaffold
                seq_info['Gene_Count'][scaffold_id] += 1
            #Do not allow duplicated sequence IDs
            if (seqobj.id in seen_ids):
                raise Exception(f'Duplicated ID: {seqobj.id} in {seq_file}')
            seen_ids[seqobj.id] = True
            if ((out_seq_file) and (seq_passed == True)):
                SeqIO.write(seqobj, OUT, "fasta")
    if (out_seq_file):
        OUT.close()
    
    print(f'Processed {seq_counter} {seq_type} sequences.')
    if (filtered_seqs > 0):
        print(f'Filtered {filtered_seqs} sequences with length outside the specified range.')

def print_results(info_dict,og_table_out_file,og_score_table_out_file,vibrant_out_quality_file,vibrant_out_amg_file,checkv_out_summary_file,vhmnet_out_dir,output_dataframe_file,merged_genomes_file,metabat_out_file,rafah_out_file):
    #Convert the 2d dictionary info_dict into a pandas dataframe and print it to output_dataframe_file in .tsv format
    info_dataframe = pd.DataFrame.from_dict(info_dict)
    info_dataframe.index.name = 'Sequence'
    #If VIBRANT was run the results should be indexed and merged to the final seq_info data frame. Do it first for the quality table
    #Notice that VIBRANT indexes the sequences by ID and Desc and appends _fragment_# to the scaffolds found as lysogens as part of longer contigs. This means that a discrepancy is created between the identifiers in Seq_Info and the VIBRANT tables
    if ((args.call_vibrant_module == True) and (vibrant_out_quality_file != 'NA')):
        vibrant_info_data_frame = index_info(vibrant_out_quality_file,'scaffold')
        lysogen_count = 0
        compiled_obj = re.compile('_fragment_(\d)+$')
        for i,row in vibrant_info_data_frame.iterrows():
            frag_match = re.search(compiled_obj,i)
            clean_name = i.split(' ')[0]
            #print('Match:',frag_match)
            if (frag_match):
                clean_name = clean_name+frag_match[0]
                lysogen_count += 1
                #print('Matched a fragment!',i,frag_match,'Updated Clean Name:',clean_name)
            vibrant_info_data_frame = vibrant_info_data_frame.rename(index={i:clean_name})
        vibrant_info_data_frame = vibrant_info_data_frame[vibrant_info_data_frame.Quality != 'complete circular']
        vibrant_info_data_frame['VIBRANT_Is_Virus'] = True
        #print('Filtered Quality Shape Is',vibrant_info_data_frame.shape,'Unique', vibrant_info_data_frame.index.is_unique)
        frames = [info_dataframe,vibrant_info_data_frame]
        info_dataframe = pd.concat(frames,axis=1)
        if (lysogen_count > 0):
            print(f'Warning! {lysogen_count} Lysogenic fragments found as part of longer scaffolds. If you are also running the index module there will be additional rows in the Seq Info file to accomodate these fragments.')
    #Now do the same but with the AMG table
    if ((args.call_vibrant_module == True) and (vibrant_out_amg_file != 'NA')):
        vibrant_info_data_frame = index_info(vibrant_out_amg_file,'protein')
        vibrant_amg_dict = defaultdict(dict)
        compiled_obj = re.compile('_fragment_(\d)+$')
        for i,row in vibrant_info_data_frame.iterrows():
            scaffold = row['scaffold']
            clean_name = scaffold.split(' ')[0]
            frag_match = re.search(compiled_obj,scaffold)
            if (frag_match):
                clean_name = clean_name+frag_match[0]
            amg_ko = row['AMG KO']
            #print(clean_name,amg_ko)
            if (clean_name not in vibrant_amg_dict['AMG_Count']):
                vibrant_amg_dict['AMG_Count'][clean_name] = 1
                vibrant_amg_dict['AMG_List'][clean_name] = [amg_ko]
            else:
                vibrant_amg_dict['AMG_Count'][clean_name]+= 1
                vibrant_amg_dict['AMG_List'][clean_name].append(amg_ko)
        
        amg_data_frame = pd.DataFrame.from_dict(vibrant_amg_dict)
        #print('AMG Shape Is',amg_data_frame.shape,'Unique', amg_data_frame.index.is_unique)
        frames = [info_dataframe,amg_data_frame]
        info_dataframe = pd.concat(frames,axis=1)
        
    #If checkV was run the results should be indexed and merged to the final seq_info data frame
    if ((args.call_checkv_module == True) and (checkv_out_summary_file != 'NA')):
        checkv_info_data_frame = index_info(checkv_out_summary_file,'contig_id')
        frames = [info_dataframe,checkv_info_data_frame]
        info_dataframe = pd.concat(frames,axis=1)
    
    #If Metabat2 was run the results should be indexed and merged to the final seq_info data frame
    if ((args.metabat2 == True)  and (metabat_out_file != 'NA')):
        metabat_info_data_frame = index_info(metabat_out_file,None,header=None)
        metabat_info_data_frame = metabat_info_data_frame.rename(columns={0: "Contig", 1: "Bin"})
        metabat_info_data_frame = metabat_info_data_frame.set_index('Contig')
        #print(metabat_info_data_frame.columns)
        frames = [info_dataframe,metabat_info_data_frame]
        info_dataframe = pd.concat(frames,axis=1)

    #If RaFAH was run the results should be indexed and merged to the final seq_info data frame
    if ((args.call_rafah == True)  and (rafah_out_file != 'NA')):
        #table_file,index_col_name,sep_var='\t',header='infer'
        rafah_info_data_frame = index_info(rafah_out_file,'Variable','\t',0)
        frames = [info_dataframe,rafah_info_data_frame]
        info_dataframe = pd.concat(frames,axis=1)
    
    #If VHMNet was run the results should be indexed and merged to the final seq_info data frame
    if ((args.call_vhmnet_module == True) and (vhmnet_out_dir != 'NA')):
        vhmnet_out_pred_files = glob.glob(f'{vhmnet_out_dir}/predictions/*csv')
        vhmnet_info_dict = defaultdict(dict)
        for pred_file in vhmnet_out_pred_files:
            scaffold = re.sub("(.)*/predictions/","",pred_file)
            scaffold = re.sub("_prediction.csv","",scaffold)
            vhmnet_info_data_frame = index_info(pred_file,'hostNCBIName',',',header=0)
            #print(pred_file,scaffold)
            for column in vhmnet_info_data_frame.columns:    
                #print(pred_file,scaffold,column,vhmnet_info_data_frame[column][0])
                if (vhmnet_info_data_frame[column][0] != 'NAmissing'):
                    vhmnet_info_dict[f'VHMNet_{column}'][scaffold] = vhmnet_info_data_frame[column][0]
        vhmnet_info_data_frame = pd.DataFrame.from_dict(vhmnet_info_dict)
        frames = [info_dataframe,vhmnet_info_data_frame]
        info_dataframe = pd.concat(frames,axis=1)
        
    #Print the dataframe with the complete seqinfo to specified file
    info_dataframe.index.name = 'Sequence'
    info_dataframe.to_csv(output_dataframe_file,sep="\t",na_rep='NA')
    
    #If specified by the user generate plots with the info collected
    if (args.make_plots_module == True):
        make_plots(info_dataframe,merged_genomes_file,args.plots_output,og_table_out_file,og_score_table_out_file,args.plots_group_var)

def explode_fasta(genome_file,split_genomes_dir):
    os.makedirs(f"{split_genomes_dir}")
    for seqobj in SeqIO.parse(genome_file, args.in_format):
        seqid = seqobj.id
        SeqIO.write(seqobj, f'{split_genomes_dir}/{seqobj.id}.fasta', "fasta")

def call_phist(genome_file="",remove_exact_matches=False,putative_host_genomes_directory="",extension_putative_host_genomes="fasta"):
    print("Running PHIST host prediction module")
    #If specified run the module to remove exact matches from putative hosts genomes
    if (remove_exact_matches == True):
        hostg_files = glob.glob(f"{putative_host_genomes_directory}/*{extension_putative_host_genomes}")
        hostg_count = len(hostg_files)
        print(f"Searching for viral Sequences from {hostg_count} host genomes")
        #Merge all host genome sequences in All_Host_Seqs.fasta. Iterate over each sequence and collect basic info
        host_seq_info = defaultdict(dict)
        host_genome_info = defaultdict(lambda: defaultdict(int))
        with open('All_Host_Seqs.fasta', 'w', newline='') as OUT:
            for hostg in hostg_files:
                #print('Processing',hostg)
                for seqobj in SeqIO.parse(hostg, 'fasta'):
                    host_genome_info['Sequence_Count'][hostg] += 1
                    host_genome_info['Bp_Count'][hostg] += len(seqobj.seq)
                    host_genome_info['Virus_List'][hostg] = set()
                    host_genome_info['Virus_Regions'][hostg] = []
                    host_seq_info["Source"][seqobj.id] = "Host"
                    host_seq_info["Genome"][seqobj.id] = hostg
                    host_seq_info["Length"][seqobj.id] = len(seqobj.seq)
                    if (args.parse_only == False):
                        SeqIO.write(seqobj, OUT, "fasta")
        #Query viral genomes against putative host genomes using BLASTN
        host_blast_db_name = build_blast_db(input_file="All_Host_Seqs.fasta")
        blast_result = call_blast(query=genome_file,ref_db=host_blast_db_name)
        #Iterate over BLASTN output and index results
        coord_info = defaultdict(dict)
        seen_pairs = defaultdict(dict)
        valid_count = 0
        for qresult in SearchIO.parse(blast_result, 'blast-tab'):
            #Iterate over hits in the query
            for hit in qresult.hits:
                #Iterate over HSPs in the hits
                for hsp in hit.hsps:
                    #Check if the HSP passes established blast cutoffs
                    viral_genome = qresult.id
                    host_seq = hit.id
                    hostg = host_seq_info["Genome"][hit.id]
                    is_valid = check_match_cutoff(hsp,0.00001,500,100,seq_info["Length"][viral_genome])
                    if ((is_valid == True) and (viral_genome not in seen_pairs[hostg].keys())):
                        host_genome_info['Prophage_Count'][hostg] += 1
                        host_genome_info['Prophage_Base_Pairs'][hostg] += seq_info["Length"][viral_genome]
                        host_genome_info['Virus_List'][hostg].add(viral_genome)
                        host_genome_info['Virus_Regions'][hostg].append(f"{host_seq}|{hsp.hit_start}|{hsp.hit_end}")
                        seen_pairs[hostg][viral_genome] = True
                        #print("Valid",viral_genome,seq_info["Length"][viral_genome],hostg,host_seq,hsp.hit_start,hsp.hit_end)
                        valid_count += 1
                        coord_info["Host_Genome"][valid_count] = hostg
                        coord_info["Host_Sequence"][valid_count] = host_seq
                        coord_info["Viral_Genome"][valid_count] = viral_genome
                        coord_info["Start_Host_Sequence"][valid_count] = int(hsp.hit_start) + 1
                        coord_info["End_Host_Sequence"][valid_count] = hsp.hit_end
                        full_sequence = False
                        if (hsp.aln_span >= host_seq_info["Length"][host_seq]):
                            full_sequence = True
                        coord_info["Full_Viral_Sequence"][valid_count] = full_sequence

        print("Printing host genome info to Host_Genomes_Info.tsv")
        hostg_info_df = pd.DataFrame.from_dict(host_genome_info)
        hostg_info_df.index.name = 'Host_Genome'
        hostg_info_df.to_csv("Host_Genomes_Info.tsv",sep="\t",na_rep=0)

        print("Printing virus exact match info to Coord_Info.tsv")
        coord_info_df = pd.DataFrame.from_dict(coord_info)
        coord_info_df.index.name = 'Match_Num'
        coord_info_df.to_csv("Coord_Info.tsv",sep="\t",na_rep=0)
        
        #Iterate over the host genome sequences removing viral sequences
        print(f"Removing viral Sequences from host genomes")
        putative_host_genomes_directory = "No_Vir_Host_Genomes/"
        os.makedirs(putative_host_genomes_directory,exist_ok=True)
        for hostg in hostg_files:
            #print('Processing',hostg)
            hostg_nid = putative_host_genomes_directory +"No_Vir_"+get_prefix(hostg,"DUMMY")
            with open(hostg_nid, 'w', newline='') as OUT:
                for seqobj in SeqIO.parse(hostg, 'fasta'):
                    original_seq = seqobj.seq
                    full_length = len(seqobj.seq)
                    index_length = full_length - 1
                    sub_coord = coord_info_df[coord_info_df["Host_Sequence"] == seqobj.id]
                    if (len(sub_coord) >= 1):
                        for i,coord in sub_coord.iterrows():
                            #print(coord)
                            start_index = int(coord["Start_Host_Sequence"]) - 1
                            stop_index = int(coord["End_Host_Sequence"]) - 1
                            full_range = list(range(0,index_length))
                            trim_range = list(range(start_index,stop_index))
                            blacklist = {posit : True for posit in trim_range}
                            trimmed_seq_nucs = []
                            for nuc_posit in full_range:
                                if nuc_posit in blacklist:
                                    trimmed_seq_nucs.append("X")
                                else:
                                    trimmed_seq_nucs.append(original_seq[nuc_posit])
                            original_seq = "".join(trimmed_seq_nucs)
                        split_seqs = re.split("(X)+",original_seq)
                        frag_count = 0 
                        for split in split_seqs:
                            frag_count += 1
                            if (len(split) > 1):
                                split_seq = SeqRecord(seq=Seq(split), id=seqobj.id+f"_Split_{frag_count}", name = seqobj.name, description=seqobj.description)
                                SeqIO.write(split_seq, OUT, "fasta")
                    else:
                        SeqIO.write(seqobj, OUT, "fasta")
        
    #Explode the fasta file of viral sequence genomes
    cwd = os.getcwd()
    explode_fasta(genome_file,split_genomes_dir=f"{cwd}/Viral_Genomes_PHIST")
    #Run PHIST
    subprocess.call(f"python3 /mnt/lustre/bio/users/fcoutinho/PHIST/phist.py -t {args.threads} Viral_Genomes_PHIST/ {putative_host_genomes_directory} PHIST_Kmers.csv PHIST_Predictions.csv",shell=True)
    #Collect results
    return("PHIST_Predictions.csv")

def get_prefix(file,extension):
    prefix_file = re.sub(f'(\.)+{extension}$','',file)
    prefix_file = re.sub('(.)+/','',prefix_file)
    return prefix_file

def build_blast_db(input_file="NA"):
    prefix_input_file = get_prefix(input_file,"(fasta)|(fa)|(fna)")
    if (args.parse_only == False):
        print('Building BLAST Nucleotide DB')
        command = f'makeblastdb -in {input_file} -dbtype nucl -title DB_{prefix_input_file} -out DB_{prefix_input_file}'
        subprocess.call(command, shell=True)
    return(f"DB_{prefix_input_file}")
    
def call_blast(query="NA",ref_db="NA"):
    prefix_query = get_prefix(query,"(fasta)|(fa)|(fna)")
    prefix_ref_db = get_prefix(ref_db,"")
    outfile = prefix_query+"x"+prefix_ref_db+".blastn"
    #Call blastn 
    if (args.parse_only == False):
        print('Performing BLASTN search')
        command = f"blastn -db {ref_db} -query {query} -out {outfile} -outfmt 6 -evalue 0.00001 -perc_identity 30 -max_target_seqs 100 -num_threads {args.threads}"
        subprocess.call(command, shell=True)
    return(outfile)

def call_virsorter2(genome_file):
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    if (args.parse_only == False):
        print('Running VirSorter2')
        command = f'virsorter run --seqfile {genome_file} --jobs {args.threads} --prep-for-dramv --rm-tmpdir'
        subprocess.call(command, shell=True)
    virsorter_out_file = "final-viral-score.tsv"
    virsorter_df = index_info(virsorter_out_file,"seqname",'\t',0)
    virsorter_df_columns = virsorter_df.columns
    compiled_obj = re.compile('\|\|full$')
    for scaffold,row in virsorter_df.iterrows():
        scaffold = re.sub(compiled_obj,'',scaffold)
        seq_info["VirSorter_Is_Virus"][scaffold] = True
        for col in virsorter_df_columns:
            seq_info[f"VirSorter_{col}"][scaffold] = row[col]


def call_bacphlip(genome_file):
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    if (args.parse_only == False):
        print('Running Bacphlip')
        command = f'bacphlip -i {genome_file} --multi_fasta'
        subprocess.call(command, shell=True)
    
    bacphlip_out_file = genome_file + '.bacphlip'
    bacphlip_df = index_info(bacphlip_out_file,0,'\t',0)
    #print(bacphlip_df.columns)
    bacphlip_df = bacphlip_df.rename(columns={"Virulent" : "Lytic_Score", "Temperate": "Temperate_Score"})
    #print(bacphlip_df.columns)
    #bacphlip_df = bacphlip_df.set_index('Scaffold')
    for scaffold,row in bacphlip_df.iterrows():
        seq_info["Bacphlip_Lytic_Score"][scaffold] = row["Lytic_Score"]
        seq_info["Bacphlip_Temperate_Score"][scaffold] = row["Temperate_Score"]
        if (row["Lytic_Score"] >= row["Temperate_Score"]):
            seq_info["Bacphlip_Classification"][scaffold] = "Lytic"
        elif (row["Lytic_Score"] < row["Temperate_Score"]):
            seq_info["Bacphlip_Classification"][scaffold] = "Lysogenic"
        
def call_vpf_class(genome_file,yaml_file):
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    if (args.parse_only == False):
        print('Running vpf-class')
        command = f'vpf-class --data-index {yaml_file} --input-seqs {genome_file} -o VPF_Class_{prefix_genome_file} --chunk-size 1000 --workers {args.threads}'
        subprocess.call(command, shell=True)
    
    vpf_outfiles = glob.glob(f'VPF_Class_{prefix_genome_file}/*tsv')
    for file in vpf_outfiles:
        var = file
        var = re.sub(f'VPF_Class_{prefix_genome_file}/','',var)
        var = re.sub('.tsv','',var)
        print ('Processing',file,var)
        vpfclass_info_data_frame = index_info(file,'virus_name','\t',0)
        for scaffold,row in vpfclass_info_data_frame.iterrows():
            mem_ratio = row['membership_ratio']
            vh_score = row['virus_hit_score']
            conf_score = row['confidence_score']
            taxon = row['class_name']
            if (scaffold not in seq_info['VPF_'+var]):
                seq_info['VPF_'+var][scaffold] = taxon
                seq_info['VPF_Membership_Ratio_'+var][scaffold] = mem_ratio
                seq_info['VPF_Confidende_Score_'+var][scaffold] = conf_score
                seq_info['VPF_Virus_Hit_Score_'+var][scaffold] = vh_score
            elif (seq_info['VPF_Membership_Ratio_'+var][scaffold] < mem_ratio):
                seq_info['VPF_'+var][scaffold] = taxon
                seq_info['VPF_Membership_Ratio_'+var][scaffold] = mem_ratio
                seq_info['VPF_Confidende_Score_'+var][scaffold] = conf_score
                seq_info['VPF_Virus_Hit_Score_'+var][scaffold] = vh_score
                
    return 0

def call_rafah(genome_file,cds_file,min_score):
    if (not cds_file):
        print('No cds file identified')
        (cds_file,gene_file,gff_file) = call_prodigal(genome_file)

    prefix_genome_file = get_prefix(genome_file,args.in_format)
    prefix_cds_file = get_prefix(cds_file,'(faa)|(fasta)|(fa)')
    if (args.parse_only == False):
        print(f'Running RaFAH')
        command = f'RaFAH_v0.2.pl --predict --merged_cds_file_name {cds_file} --min_cutoff {min_score} --threads {args.threads} --file_prefix RaFAH_{prefix_cds_file}'
        print(command)
        subprocess.call(command, shell=True)
    
    rafah_out_file = f'RaFAH_{prefix_cds_file}'+'_Seq_Info_Prediction.tsv'
    return rafah_out_file
        
    
def align_protein_to_hmm(cds_file,db_file,out_file,threads):
    #Align proteins against the generated hmm 
    print(f'Querying {cds_file} against {db_file}')
    command = f'hmmsearch -o {out_file} --noali --cpu {threads} {db_file} {cds_file}'
    subprocess.call(command, shell=True)                
    return(1)
    
def call_hmmer (cds_file,db_file,program):
    cds_file_prefix = get_prefix(cds_file,'(faa)|(fasta)|(fa)')
    db_file_prefix = get_prefix(db_file,'hmm')
    outfile = 'NA'
    if (program == 'hmmscan'):
        outfile = cds_file_prefix+'x'+db_file_prefix+'.hmmscan'
        if (args.parse_only == False):
            print(f'Querying {db_file} against {cds_file}')
            command = f'hmmscan -o {outfile} --noali --cpu {args.threads} {db_file} {cds_file}'
            subprocess.call(command, shell=True)
    elif (program == 'hmmsearch'):
        outfile = cds_file_prefix+'x'+db_file_prefix+'.hmmsearch'
        if (args.parse_only == False):
            print(f'Querying {cds_file} against {db_file}')
            command = f'hmmsearch -o {outfile} --noali --cpu {args.threads} {db_file} {cds_file}'
            subprocess.call(command, shell=True)    
    else:
        print('Not a valid Hmmer program!')
        
    return outfile

def calc_pps(genome_file,cds,pps_subject_fasta,pps_subject_db,precomp_hits_table):
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    prefix_subject_fasta_file = get_prefix(pps_subject_fasta,'(faa)|(fasta)|(fa)')
    prefix_subject_DB_file = get_prefix(pps_subject_db,args.in_format)
    prefix_cds_file = get_prefix(cds,'(faa)|(fasta)|(fa)')
    index_seqs([genome_file],cds,False,'NA',False)
    outfile = 'NA'
    if (precomp_hits_table != "NA"):
        outfile = precomp_hits_table
    else:
        if (pps_subject_db == 'NA'):
            outfile = f'{prefix_cds_file}x{prefix_subject_fasta_file}.m8'
            command = f'mmseqs easy-search {cds} {pps_subject_fasta} {outfile} tmp --threads {args.threads} --max-seqs 1000 --min-seq-id 0.3 --min-aln-len 30'
            subprocess.call(command, shell=True)
        else:
            outfile = f'{prefix_cds_file}x{prefix_subject_DB_file}.m8'
            command = f'mmseqs easy-search {cds} {pps_subject_db} {outfile} tmp --threads {args.threads} --max-seqs 1000 --min-seq-id 0.3 --min-aln-len 30'
            subprocess.call(command, shell=True)
    recip_scores = calc_recip_scores(outfile)
    recip_scores_file = outfile+'.Pairwise_Protein_Scores.tsv'
    print_scores(recip_scores,recip_scores_file,args.pps_min_aai,args.pps_min_matched,args.pps_min_perc_matched)

def print_scores(recip_scores,recip_scores_file,min_aai,min_matched,min_perc_matched):
    print(f'Printing Pairwise Protein Scores to {recip_scores_file}')
    with open(recip_scores_file, 'w', newline='') as OUT:
        OUT.write('Query_Scaffold\tSubject_Scaffold\tAAI\tMatched_CDS\tPerc_Matched_CDS\n')
        for genomeA in recip_scores['Matched_CDS'].keys():
            for genomeB in recip_scores['Matched_CDS'][genomeA].keys():
                #check_vp_cutoff(pair_ani,pair_matched,pair_perc_matched,cutoff_ani,cutoff_matched,cutoff_perc_matched)
                is_valid = check_vp_cutoff(recip_scores['AAI'][genomeA][genomeB],recip_scores['Matched_CDS'][genomeA][genomeB],recip_scores['Perc_Matched_CDS'][genomeA][genomeB],min_aai,min_matched,min_perc_matched)
                if (is_valid == True):
                    line_list = [genomeA,genomeB,recip_scores['AAI'][genomeA][genomeB],recip_scores['Matched_CDS'][genomeA][genomeB],recip_scores['Perc_Matched_CDS'][genomeA][genomeB]]
                    line = '\t'.join(str(field) for field in line_list)
                    OUT.write(f'{line}\n')
            
def calc_recip_scores(infile):
    #Initialize 2D dictionary that will hold the reciprocal scores
    recip_scores = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    #Parse the m8 file
    print ('Parsing m8 output',infile)
    #Seen hits will keep track of the seen CDS pairs so to not overestimate AAI and Perc matched genes
    seen_hits = defaultdict(dict)
    #Iterare over queries
    for qresult in SearchIO.parse(infile, 'blast-tab'):
        #Iterate over hits in the query
        for hit in qresult.hits:
            #Iterate over HSPs in the hits
            for hsp in hit.hsps:
                #Check if the HSP passes established blast cutoffs
                is_valid = check_match_cutoff(hsp,0.001,30,0.3,30)
                if (is_valid):
                    #Derive the original scaffold name from the CDS id
                    genomeA = re.sub('_(\d)+$','',qresult.id)
                    genomeB = re.sub('_(\d)+$','',hit.id)
                    #Only go on if matches are between two different scaffolds and two different CDS
                    if ((genomeA != genomeB) and (qresult.id != hit.id)):
                        #Only go on if the query/hit pair has not been processed before
                        if (genomeB not in seen_hits[qresult.id].keys()):
                            seen_hits[qresult.id][genomeB] = 1
                            recip_scores['Matched_CDS'][genomeA][genomeB] += 1
                            recip_scores['Perc_Matched_CDS'][genomeA][genomeB] += ((1 / seq_info['CDS_Count'][genomeA]) * 100)
                            recip_scores['ID_Sum'][genomeA][genomeB] += (hsp.ident_pct * 100)
    
    #Calculate AAI between genome pairs
    print('Calculating AAI')
    for genomeA in recip_scores['Matched_CDS'].keys():
        for genomeB in recip_scores['Matched_CDS'][genomeA].keys():
            recip_scores['AAI'][genomeA][genomeB] = recip_scores['ID_Sum'][genomeA][genomeB] / recip_scores['Matched_CDS'][genomeA][genomeB]
    
    return (recip_scores)
                            
    


def call_spades(raw_read_table="",spades_memory=250):
    raw_read_info_df = index_info(raw_read_table,"Sample",'\t',header=0)
    scaffold_files = []
    if (not raw_read_info_df.empty):
        for group in set(raw_read_info_df['Group']):
            print(f"Processing samples from group {group}")
            group_df = raw_read_info_df[raw_read_info_df['Group'] == group]
            samples_list = group_df.index
            print(f"Assembling sample(s): {samples_list}")
            r1_files = list(group_df['R1'])
            r1_files = ' -1 '.join(r1_files)
            r2_files = list(group_df['R2'])
            r2_files = ' -2 '.join(r2_files)
            command = f'spades.py -1 {r1_files} -2 {r2_files} -o Assembly_{group} --threads {args.threads} --memory {spades_memory} --meta'
            if (args.parse_only == False):
                print(f"Running: {command}")
                subprocess.call(command, shell=True)
            out_file = f'Assembly_{group}/scaffolds.fasta'
            scaffold_files.append(out_file)
    index_seqs(scaffold_files,'',True,'Merged_Scaffolds.fasta',True)
    filter_seqs('Merged_Scaffolds.fasta',1000,999999999)
    return('Filtered_Merged_Scaffolds.fasta')

def calc_abundance(genome_file,db_file,metagenomes_dir,metagenomes_extension,max_reads,bowtie_mode,min_count,raw_read_table):
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    raw_abund_matrix = pd.DataFrame()
    
    db_file_prefix = 'NA'
    if (db_file == 'NA'):
        print(f'Building Bowtie2 database from {genome_file}')
        command = f'bowtie2-build --threads {args.threads} {genome_file} {prefix_genome_file}'
        db_file = prefix_genome_file
        db_file_prefix = prefix_genome_file
        subprocess.call(command, shell=True)
    else:
        db_file_prefix = get_prefix(db_file,"DUMMY")
    

    raw_read_info_df = index_info(raw_read_table,"Sample",'\t',header=0)
    
    if (not raw_read_info_df.empty):
        for group in set(raw_read_info_df['Group']):
            print(f"Processing samples from group {group}")
            group_df = raw_read_info_df[raw_read_info_df['Group'] == group]
            samples_list = group_df.index
            print(f"Aligning reads from sample(s): "+str(",".join(set(samples_list))))
            r1_files = list(group_df['R1'])
            r1_files = ' -1 '.join(r1_files)
            r2_files = list(group_df['R2'])
            r2_files = ' -2 '.join(r2_files)
            outfile = group+'x'+db_file_prefix
            command = f"bowtie2 -x {db_file} -q -1 {r1_files} -2 {r2_files} -S {outfile}.sam --{bowtie_mode} --no-discordant --no-mixed --no-unal --threads {args.threads}"
            if (max_reads > 0):
                command = command + f" -u {max_reads}"
            if (args.bowtie_k > 0):
                command = command + f" -k {args.bowtie_k}"
            if (args.parse_only == False):
                print(f"Running: {command}")
                subprocess.call(command, shell=True)
            if (args.parse_only == False):
                command = f'samtools view -bS {outfile}.sam > {outfile}.bam'
                subprocess.call(command, shell=True)
                command = f'samtools sort {outfile}.bam -o {outfile}.sorted.bam'
                subprocess.call(command, shell=True)
                command = f'rm -f {outfile}.sam {outfile}.bam'
                subprocess.call(command, shell=True)
                command = f'samtools index {outfile}.sorted.bam'
                subprocess.call(command, shell=True)
                command = f'samtools idxstats {outfile}.sorted.bam > {outfile}.Counts.tsv'
                subprocess.call(command, shell=True)
            sample_abund = index_info(f'{outfile}.Counts.tsv',None,'\t',header=None)
            sample_abund = sample_abund.rename(columns={0: "Sequence", 1: "Length",2: group, 3: "Unmapped"})
            sample_abund = sample_abund.set_index('Sequence')
            sample_abund.drop(sample_abund.tail(1).index,inplace=True)
            if (min_count > 0):
                sample_abund.loc[sample_abund[group] < min_count, group] = 0
            frames = [raw_abund_matrix,sample_abund[group]]
            raw_abund_matrix = pd.concat(frames,axis=1)
        #print(raw_abund_matrix.shape)
    
    raw_abund_matrix_file = 'Raw_Abundance_'+f'{prefix_genome_file}.tsv'
    raw_abund_matrix.index.name = 'Sequence'
    raw_abund_matrix = raw_abund_matrix.div(2,axis=0)
    raw_abund_matrix.to_csv(raw_abund_matrix_file,sep="\t",na_rep='NA')
    
    if (args.abundance_rpkm == True):
        #Calc perc abundance
        print("Calculating percentage abundance")
        perc_abund_matrix_file = 'Percentage_Abundance_'+f'{prefix_genome_file}.tsv'
        #perc_abund_matrix = (raw_abund_matrix / raw_abund_matrix.sum(axis=1)) * 100
        perc_abund_matrix = (raw_abund_matrix.div(raw_abund_matrix.sum(axis=0),axis=1)) * 100
        perc_abund_matrix.to_csv(perc_abund_matrix_file,sep="\t",na_rep='NA')
        #Calc RPKM
        print("Calculating RPKM abundance")
        seq_info_matrix = pd.DataFrame.from_dict(seq_info)
        #Reindex seq_info_matrix in case the orders of sequences differ between seq_info_matrix and raw_abund_matrix
        seq_info_matrix = seq_info_matrix.reindex(raw_abund_matrix.index.values)
        rpkm_abund_matrix_file = 'RPKM_Abundance_'+f'{prefix_genome_file}.tsv'
        rpkm_abund_matrix = (raw_abund_matrix.div((seq_info_matrix['Length'] / 1000),axis=0)  / (raw_abund_matrix.sum(axis=0) / 1000000))
        rpkm_abund_matrix.index.name = 'Sequence'
        rpkm_abund_matrix.to_csv(rpkm_abund_matrix_file,sep="\t",na_rep='NA')

    
def index_samples(metagenomes_dir,metagenomes_extension,count_reads):
    samples_index = defaultdict(dict)
    for directory in metagenomes_dir:
        print(f"Looking for files in {directory}")
        files = glob.glob(f'{directory}/*{metagenomes_extension}')
        print("Found files:",files)

        for file in files:
            if (re.search('_1',file)):
                sample_id = file
                sample_id = re.sub('(.)*/','',sample_id)
                sample_id = re.sub(f'_1(\.)*{metagenomes_extension}','',sample_id)
                pair = file
                pair = re.sub('_1','_2',pair)
                samples_index[sample_id]['R1'] = file
                samples_index[sample_id]['R2'] = pair
                samples_index[sample_id]['Is_Paired'] = True
                print(sample_id,'R1',file,'R2',pair)
        
    return(samples_index)
            
def call_metabat(genome_file):
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    metabat_out_file = f'Binning_{prefix_genome_file}'
    command = f'metabat2 -i {genome_file} -s 10000 -l --saveCls -o {metabat_out_file} -t {args.threads} --noBinOut'
    subprocess.call(command, shell=True)
    return(metabat_out_file)
    
def make_og_score_table_and_phylogeny(genome_file,cds_file,min_cluster_size,make_score_table,make_phylogeny):
    print('Running Orthologous Group Score table module')
    #check if there is a CDS file. Otherwise run prodigal
    if (not cds_file):
        print('No cds file identified')
        (cds_file,gene_file,gff_file) = call_prodigal(genome_file)
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    #Cluster CDS sequences into OGs
    out_mmseqs_cluster_file = call_mmseqs_cluster(cds_file,prefix_genome_file,args.threads)
    #Parse the output of mmseqs and store Genome x OG count info in og_table
    (og_table,protein_info,cluster_info) = parse_mmseqs_cluster_file(out_mmseqs_cluster_file)

    #Print output to og_table_out_file
    og_table_out_file = 'OG_Table_'+prefix_genome_file+'.tsv'
    og_table_data_frame = pd.DataFrame.from_dict(og_table)
    print(f'Printing OG table to {og_table_out_file}')
    og_table_data_frame.to_csv(og_table_out_file,sep="\t",na_rep=0)
    
    
    #Split sequences by OG affiliation
    unaligned_cluster_dir = 'Unaligned_Clusters_'+prefix_genome_file
    command = f'mkdir {unaligned_cluster_dir}'
    subprocess.call(command, shell=True)
    #Create a directory to store aligned fasta file of clusters
    aligned_cluster_dir = 'Aligned_Clusters_'+prefix_genome_file
    command = f'mkdir {aligned_cluster_dir}'
    subprocess.call(command, shell=True)
    #Create a directory to store the HMMs
    hmm_cluster_dir = 'Hmm_Aligned_Clusters_'+prefix_genome_file
    if (make_score_table == True):
        command = f'mkdir {hmm_cluster_dir}'
        subprocess.call(command, shell=True)
    #Create a directory to store the phylogenies
    phylo_cluster_dir = 'Phylogenies_Aligned_Clusters_'+prefix_genome_file
    if (make_phylogeny == True):
        command = f'mkdir {phylo_cluster_dir}'
        subprocess.call(command, shell=True)
    
    for seqobj in SeqIO.parse(cds_file, 'fasta'):
        #Collect description and legth information and store it in protein_info
        #protein_info['Description'][seqobj.id] = seqobj.description
        #protein_info['Length'][seqobj.id] = len(seqobj.seq)
        #print(seqobj.id, protein_info['OG'].keys())
        prot_cluster = protein_info['OG'][seqobj.id]
        #Print the sequence to its cluster file if the cluster meets the criteria for minimum number of members
        if (cluster_info['Members'][prot_cluster] >= min_cluster_size):
            fasta_cluster_name = f'{unaligned_cluster_dir}/Unaligned_Cluster_'+prot_cluster+'.faa'
            fasta_handle = open(fasta_cluster_name, "a+")
            SeqIO.write(seqobj,fasta_handle, "fasta")
            fasta_handle.close()
    
    
    for prot_cluster in cluster_info['Members'].keys():
        #Skip clusters that do not meet the criteria for minimum size
        if (cluster_info['Members'][prot_cluster] >= min_cluster_size):
            #Align cluster with muscle
            command = f'muscle -in {unaligned_cluster_dir}/Unaligned_Cluster_{prot_cluster}.faa -out {aligned_cluster_dir}/Aligned_Cluster_{prot_cluster}.faa -quiet'
            subprocess.call(command, shell=True)
            if (make_score_table == True):
                #Build HMM from alignment
                command = f'hmmbuild -n {prot_cluster} {hmm_cluster_dir}/Aligned_Cluster_{prot_cluster}.hmm {aligned_cluster_dir}/Aligned_Cluster_{prot_cluster}.faa'
                subprocess.call(command, shell=True)
            if (make_phylogeny == True):
                command = f"FastTreeMP -nosupport -out {phylo_cluster_dir}/Tree_Aligned_Cluster_{prot_cluster}.newick {aligned_cluster_dir}/Aligned_Cluster_{prot_cluster}.faa"
                subprocess.call(command, shell=True)

    og_score_table_out_file = 'OG_Score_Table_'+prefix_genome_file+'.tsv'
    
    if (make_score_table == True):
        #Merge all HMMs into a single file
        concat_hmmer_file = 'All_Clusters_'+prefix_genome_file+'.hmm'
        command = f'cat {hmm_cluster_dir}/*.hmm > {concat_hmmer_file}'
        subprocess.call(command, shell=True)
        #Run HMMpress on the merged hmm file
        print('Building HMM database')
        command = f'hmmpress {concat_hmmer_file}'
        subprocess.call(command, shell=True)
        hmmer_out_file = prefix_genome_file+'xAll_Clusters'
        align_protein_to_hmm(cds_file,concat_hmmer_file,hmmer_out_file,args.threads)
        (genome_hmm_scores,pairwise_scores) = parse_hmmer_output(hmmer_out_file)
        
        #Print genome_hmm_scores to og_score_table_out_file
        og_score_table_data_frame = pd.DataFrame.from_dict(genome_hmm_scores)
        og_score_table_data_frame.index.name = 'Sequence'
        print(f'Printing OG x Genome score table to {og_score_table_out_file}')
        og_score_table_data_frame.to_csv(og_score_table_out_file,sep="\t",na_rep=0)
        
        #Print pairwise_scores to og_score_table_out_file
        pairwise_score_table_out_file = 'OG_Pairwise_Score_Table_'+prefix_genome_file+'.tsv'
        pairwise_score_table_data_frame = pd.DataFrame.from_dict(pairwise_scores)
        print(f'Printing OG x CDS pairwise scores table to {pairwise_score_table_out_file}')
        pairwise_score_table_data_frame.to_csv(pairwise_score_table_out_file,sep="\t",na_rep='NA')
    
    return(og_score_table_out_file)

def parse_mmseqs_cluster_file(out_mmseqs_cluster_file):
    print(f'Parsing {out_mmseqs_cluster_file}')
    og_table = defaultdict(lambda: defaultdict(int))
    protein_info = defaultdict(dict)
    cluster_info = defaultdict(dict)
    #Output file is a .tsv where OG is the first column and cds is the scond
    lines = open(out_mmseqs_cluster_file,"r").readlines()
    compiled_obj = re.compile('\W')
    for line in lines:
        (og,cds) = line.split('\t')
        og = re.sub(compiled_obj,'_',og)
        protein_info['OG'][cds.rstrip()] = og
        genome = re.sub('_(\d)+$','',cds)
        genome = genome.rstrip()
        og_table[og][genome]+= 1
        #Create OG_Count field in seq info for the genome if it is not already there
        if (genome not in seq_info['OG_Count'].keys()):
            seq_info['OG_Count'][genome] = 0
        seq_info['OG_Count'][genome] += 1
        #print(og,genome)
        if (og not in cluster_info['Members'].keys()):
            cluster_info['Members'][og] = 0
        cluster_info['Members'][og] += 1
    
    return(og_table,protein_info,cluster_info)

def parse_hmmer_output(hmmer_out_file,max_evalue=0.001,min_score=50):
    genome_hmm_scores = defaultdict(dict)
    pairwise_scores = defaultdict(dict)
    hsp_count = 0
    #Parse the output
    print(f'Parsing {hmmer_out_file}')
    #Iterate over each query
    for qresult in SearchIO.parse(hmmer_out_file, 'hmmer3-text'):
        #Iterate over each Hit
        for hit in qresult.hits:
            #Iterate over each HSP
            for hsp in hit.hsps:
                genome = hit.id
                genome = re.sub('_(\d)+$','',genome)
                #print(qresult.id,genome,hit.id)
                is_valid = check_hmmer_match_cutoff(hsp,max_evalue,min_score)
                if is_valid:
                    hsp_count += 1
                    pairwise_scores['Genome'][hsp_count] = genome
                    pairwise_scores['Query'][hsp_count] = qresult.id
                    pairwise_scores['Subject'][hsp_count] = hit.id
                    pairwise_scores['Score'][hsp_count] = hsp.bitscore
                    pairwise_scores['e-value'][hsp_count] = hsp.evalue
                    pairwise_scores['Subject_Description'][hsp_count] = hit.description
                    pairwise_scores['Query_Description'][hsp_count] = qresult.description
                    ori_score = genome_hmm_scores[qresult.id].get(genome,0)
                    if (ori_score < hsp.bitscore):
                        genome_hmm_scores[qresult.id][genome] = hsp.bitscore
                        
    return(genome_hmm_scores,pairwise_scores)
    
def make_og_table(genome_file,cds_file):
    print('Running Orthologous Group count table module')
    #check if there is a CDS file. Otherwise run prodigal
    if (not cds_file):
        print('No cds file identified')
        (cds_file,gene_file,gff_file) = call_prodigal(genome_file)
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    #Cluster CDS sequences into OGs
    out_mmseqs_cluster_file = call_mmseqs_cluster(cds_file,prefix_genome_file,args.threads)
    #Parse the output of mmseqs and store Genome x OG count info in og_table
    (og_table,protein_info,cluster_info) = parse_mmseqs_cluster_file(out_mmseqs_cluster_file)
    og_table_out_file = 'OG_Count_Table_'+prefix_genome_file+'.tsv'
    og_table_data_frame = pd.DataFrame.from_dict(og_table)
    og_table_data_frame.index.name = 'Sequence'
    print(f'Printing OG table to {og_table_out_file}')
    og_table_data_frame.to_csv(og_table_out_file,sep="\t",na_rep=0)
    return(og_table_out_file)
    
def call_mmseqs_cluster(cds_file,prefix_genome_file,threads):
    print('Running mmseqs easy-cluster')
    command = f'mmseqs easy-cluster {cds_file} {prefix_genome_file} tmp --threads {threads} -c 0.3 -s 7.5 --min-seq-id 0.25 --cov-mode 0'
    subprocess.call(command, shell=True)
    out_mmseqs_cluster_file = prefix_genome_file+'_cluster.tsv'
    return out_mmseqs_cluster_file
        
def make_pops(genome_file,gene_file):
    print('Clustering sequences into viral populations')
    #check if there is a genes file. Otherwise run prodigal
    if (not gene_file):
        print('No gene file identified')
        (cds_file,gene_file,gff_file) = call_prodigal(genome_file)
        #Index the length and CDS_Count of the genomic sequences. This will be necessary when clustering the VPs
        index_seqs([],gene_file,False,'NA',False)
        
    #Build blast db of the genes file
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    blastn_out_file_name = prefix_genome_file+'xSelf.blastn'
    if (args.parse_only == False):
        print('Building BLAST Nucleotide DB')
        command = f'makeblastdb -in {gene_file} -dbtype nucl -title DB_{prefix_genome_file} -out DB_{prefix_genome_file}'
        subprocess.call(command, shell=True)
        #Call blastn 
        print('Performing BLASTN search')
        command = f"blastn -db DB_{prefix_genome_file} -query {gene_file} -out {blastn_out_file_name} -outfmt 6 -evalue 0.001 -perc_identity 30 -max_target_seqs 999999 -num_threads {args.threads}"
        subprocess.call(command, shell=True)
    
    #Parse the output of BLASTN
    print ('Parsing BLASTN output',blastn_out_file_name)
    #Seen hits will keep track of the seen CDS pairs so to not overestimate ANI and Perc matched genes
    seen_hits = defaultdict(dict)
    scores = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    #Iterare over queries
    for qresult in SearchIO.parse(blastn_out_file_name, 'blast-tab'):
        #Iterate over hits in the query
        for hit in qresult.hits:
            #Iterate over HSPs in the hits
            for hsp in hit.hsps:
                #Check if the HSP passes established blast cutoffs
                is_valid = check_match_cutoff(hsp,0.001,30,30,30)
                if (is_valid):
                    #Derive the original scaffold name from the CDS id
                    genomeA = re.sub('_(\d)+$','',qresult.id)
                    genomeB = re.sub('_(\d)+$','',hit.id)
                    #Only go on if matches are between two different scaffolds and two different CDS
                    if ((genomeA != genomeB) and (qresult.id != hit.id)):
                        #print(genomeA,genomeB,hsp)
                        #Only go on if the query/hit pair has not been processed before
                        if (genomeB not in seen_hits[qresult.id].keys()):
                            seen_hits[qresult.id][genomeB] = 1
                            scores['Matched_CDS'][genomeA][genomeB] += 1
                            scores['Perc_Matched_CDS'][genomeA][genomeB] += ((1 / seq_info['CDS_Count'][genomeA]) * 100)
                            scores['ID_Sum'][genomeA][genomeB] += hsp.ident_pct
                            #initialize variables in the scores dictionary if they are not there already
                            
            
    
    #Now that the output of BLASTN has been parsed move forward to calculate the ANI by iterating through scores
    pop_counter = 0
    print ('Calculating sequence match scores and assigning populations')
    #iterate over genomes ordered by their Length
    for genomeA in sorted(seq_info['Length'], key=seq_info['Length'].get, reverse=True):
        #print(genomeA,seq_info['Length'][genomeA])
        #If genomeA has not been assigned to a population yet, increment pop_counter and assign genome A to that population
        if (genomeA not in seq_info['Population'].keys()):
            pop_counter += 1
            seq_info['Population'][genomeA] = 'VP_'+str(pop_counter)
            seq_info['Population_Representative'][genomeA] = True
        #Now iterate over all genomes that have matches to genomeA
        for genomeB in scores['ID_Sum'][genomeA].keys():
            #Only consider those pairs for which genomeB has not been assigned to a population and that have a defined Matched_CDS count in scores
            if ((genomeB not in seq_info['Population'].keys()) and (scores['Matched_CDS'][genomeB][genomeA] > 0)  and (scores['Matched_CDS'][genomeA][genomeB] > 0)):
                #Calculate ANI now that the ID_SUM and Matched CDS are complete
                scores['ANI'][genomeB][genomeA] = scores['ID_Sum'][genomeB][genomeA] / scores['Matched_CDS'][genomeB][genomeA]
                #print(genomeA,seq_info['Length'][genomeA],genomeB,scores['ANI'][genomeB][genomeA],scores['Perc_Matched_CDS'][genomeB][genomeA])
                #Test if the scores of ANI and Perc matched CDS pass the cutoffs
                is_same_vp = check_vp_cutoff(scores['ANI'][genomeB][genomeA],scores['Matched_CDS'][genomeB][genomeA],scores['Perc_Matched_CDS'][genomeB][genomeA],95,3,80)
                if (is_same_vp):
                    #print(genomeA,seq_info['Length'][genomeA],genomeB,scores['ANI'][genomeA][genomeB],scores['Perc_Matched_CDS'][genomeA][genomeB])
                    #If is within the cutoff to assign to the same VP, assing genomeB to the same VP as genomeA
                    seq_info['Population'][genomeB] = seq_info['Population'][genomeA]
                    seq_info['Population_Representative'][genomeB] = False
    return 1

def check_vp_cutoff(pair_ani,pair_matched,pair_perc_matched,cutoff_ani,cutoff_matched,cutoff_perc_matched):    
    if ((pair_ani < cutoff_ani) or (pair_matched < cutoff_matched) or (pair_perc_matched < cutoff_perc_matched)):
        return False
    else:
        return True
        
def check_match_cutoff(hsp,max_evalue,min_bitscore,min_ident,min_ali):
    if ((hsp.bitscore < min_bitscore) or (hsp.evalue > max_evalue) or (hsp.ident_pct < min_ident) or (hsp.aln_span < min_ali)):
        return False
    else:
        return True

def check_hmmer_match_cutoff(hsp,max_evalue,min_bitscore):
    if ((hsp.bitscore < min_bitscore) or (hsp.evalue > max_evalue)):
        return False
    else:
        return True
        
def call_vhmnet(genome_file):
    print("Running viral host prediction with VirHostMatcher-Net")
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    vhmnet_out_dir = 'VHMNet_Output_'+prefix_genome_file
    if (args.parse_only == False):
        split_genomes_dir = 'Split_Genomes_'+prefix_genome_file
        explode_fasta(genome_file,split_genomes_dir)
        subprocess.call(f'mkdir {vhmnet_out_dir}', shell=True)
        if (args.vhmnet_mode_short):
            command = f'VirHostMatcher-Net.py -q {split_genomes_dir} -o {vhmnet_out_dir} -t {args.threads} -i tmp -n 10 --short-contig'
        else:
            command = f'VirHostMatcher-Net.py -q {split_genomes_dir} -o {vhmnet_out_dir} -t {args.threads} -i tmp -n 10'
        subprocess.call(command, shell=True)
    return(vhmnet_out_dir)

def call_checkv(genome_file):
    print("Running viral sequence quality checking with CheckV")
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    checkv_out_dir = 'CheckV_'+prefix_genome_file
    command = f'checkv end_to_end {genome_file} {checkv_out_dir} -t {args.threads}'
    subprocess.call(command, shell=True)
    checkv_out_summary_file = f'{checkv_out_dir}/quality_summary.tsv'
    return checkv_out_summary_file

def index_info(table_file,index_col_name,sep_var='\t',header='infer'):
    print(f'Reading info from {table_file}')
    info_data_frame = pd.read_csv(table_file, sep=sep_var,index_col=index_col_name,header=header)
    return info_data_frame
    
def call_vibrant(genome_file):
    #Run VIBRANT with default parameters
    if (args.parse_only == False):
        print("Running virus identification with VIBRANT")
        command = f'VIBRANT_run.py -i {genome_file} -t {args.threads}'
        subprocess.call(command, shell=True)
    prefix_genome_file = get_prefix(genome_file,args.in_format)
    vibrant_out_dir = 'VIBRANT_'+prefix_genome_file+'/VIBRANT_results_'+prefix_genome_file
    vibrant_out_quality_file = f'{vibrant_out_dir}/VIBRANT_genome_quality_{prefix_genome_file}.tsv'
    vibrant_out_amg_file = f'{vibrant_out_dir}/VIBRANT_AMG_individuals_{prefix_genome_file}.tsv'
    return(vibrant_out_quality_file,vibrant_out_amg_file)
    
def call_prodigal(genome_file="All_Genomic.fasta"):
    print("Running gene calling with Prodigal")
    #Define the prefix of the genome file (i.e. remove the extension). Create names for the cds, gene and dff file based on the prefix. Call prodigal. Return names of generated files
    #prefix_genome_file = get_prefix(genome_file,args.in_format)
    #cds_file = "All_CDS.faa" #prefix_genome_file+'.faa'
    #gene_file = prefix_genome_file+'.fna'
    #gff_file = prefix_genome_file+'.gff'
    cds_file = 'All_CDS.faa'
    gene_file = 'All_Genes.fasta'
    gff_file = 'All_Genomic.gff'
    if (args.parse_only == False):
        command = f'prodigal -q -p meta -a {cds_file} -d {gene_file} -f gff -i {genome_file} -o {gff_file}'
        subprocess.call(command, shell=True)
    return(cds_file,gene_file,gff_file)

def make_plots(info_dataframe,merged_genomes_file,output_figure_file,og_table_out_file,og_score_table_out_file,group_var):
    print('Running plotting module')
    prefix_genome_file = get_prefix(merged_genomes_file,args.in_format)
    
    info_dataframe['Group'] = 'All'
    valid_vars = ['Length','GC','completeness','contamination','CDS_Count','score','hostPhylum','Population','OG_Count','Bin','AMG_Count','Predicted_Host','VPF_baltimore','VPF_family','VPF_genus']#,'VPF_host_domain','VPF_host_family','VPF_host_genus'
    axis_count = 0
    axis_dict = {}
    for var in valid_vars:
        if (var in info_dataframe):
            axis_count+= 1
            axis_dict[var] = axis_count - 1

        
    sns.set_theme(font='serif')
    ideal_width = 4.25*axis_count
    composite_plot, axes = plt.subplots(nrows=1,ncols=axis_count,figsize=[ideal_width,8])

    #Generate different types of plots according to the data available in seq_info
    if ('GC' in axis_dict):
        gc_hist_plot = sns.histplot(ax=axes[axis_dict['GC']],data=info_dataframe,x="GC", bins=20,hue=group_var)
    if ('Length' in axis_dict):
        length_hist_plot = sns.histplot(ax=axes[axis_dict['Length']],data=info_dataframe,x="Length", bins=20,hue=group_var)
    if ('completeness' in axis_dict):
        comp_hist_plot = sns.histplot(ax=axes[axis_dict['completeness']],data=info_dataframe,x="completeness", bins=20,hue=group_var)
    if ('contamination' in axis_dict):
        conta_hist_plot = sns.histplot(ax=axes[axis_dict['contamination']],data=info_dataframe,x="contamination", bins=20,hue=group_var)
    if ('CDS_Count' in axis_dict):
        genecount_hist_plot = sns.histplot(ax=axes[axis_dict['CDS_Count']],data=info_dataframe,x="CDS_Count", bins=20,hue=group_var)
    if ('score' in axis_dict):
        score_hist_plot = sns.histplot(ax=axes[axis_dict['score']],data=info_dataframe,x="score", bins=20,hue=group_var)
    if ('OG_Count' in axis_dict):
        ogcount_hist_plot = sns.histplot(ax=axes[axis_dict['OG_Count']],data=info_dataframe,x="OG_Count", bins=20,hue=group_var)
    if ('AMG_Count' in axis_dict):
        ogcount_hist_plot = sns.histplot(ax=axes[axis_dict['AMG_Count']],data=info_dataframe,x="AMG_Count", bins=20,hue=group_var)
    if ('hostPhylum' in axis_dict):
        hphy_count_plot = sns.countplot(ax=axes[axis_dict['hostPhylum']],x="hostPhylum", data=info_dataframe)
        hphy_count_plot.set_xticklabels(hphy_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('Predicted_Host' in axis_dict):
        rafah_count_plot = sns.countplot(ax=axes[axis_dict['Predicted_Host']],x="Predicted_Host", data=info_dataframe, order=pd.value_counts(info_dataframe['Predicted_Host']).iloc[:10].index)
        rafah_count_plot.set_xticklabels(rafah_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('VPF_baltimore' in axis_dict):
        rafah_count_plot = sns.countplot(ax=axes[axis_dict['VPF_baltimore']],x="VPF_baltimore", data=info_dataframe, order=pd.value_counts(info_dataframe['VPF_baltimore']).iloc[:10].index)
        rafah_count_plot.set_xticklabels(rafah_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('VPF_family' in axis_dict):
        rafah_count_plot = sns.countplot(ax=axes[axis_dict['VPF_family']],x="VPF_family", data=info_dataframe, order=pd.value_counts(info_dataframe['VPF_family']).iloc[:10].index)
        rafah_count_plot.set_xticklabels(rafah_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('VPF_genus' in axis_dict):
        rafah_count_plot = sns.countplot(ax=axes[axis_dict['VPF_genus']],x="VPF_genus", data=info_dataframe, order=pd.value_counts(info_dataframe['VPF_genus']).iloc[:10].index)
        rafah_count_plot.set_xticklabels(rafah_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('VPF_host_domain' in axis_dict):
        rafah_count_plot = sns.countplot(ax=axes[axis_dict['VPF_host_domain']],x="VPF_host_domain", data=info_dataframe, order=pd.value_counts(info_dataframe['VPF_host_domain']).iloc[:10].index)
        rafah_count_plot.set_xticklabels(rafah_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('VPF_host_family' in axis_dict):
        rafah_count_plot = sns.countplot(ax=axes[axis_dict['VPF_host_family']],x="VPF_host_family", data=info_dataframe, order=pd.value_counts(info_dataframe['VPF_host_family']).iloc[:10].index)
        rafah_count_plot.set_xticklabels(rafah_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('VPF_host_genus' in axis_dict):
        rafah_count_plot = sns.countplot(ax=axes[axis_dict['VPF_host_genus']],x="VPF_host_genus", data=info_dataframe, order=pd.value_counts(info_dataframe['VPF_host_genus']).iloc[:10].index)
        rafah_count_plot.set_xticklabels(rafah_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('Population' in axis_dict):
        pop_count_plot = sns.countplot(ax=axes[axis_dict['Population']],x="Population", data=info_dataframe, order=pd.value_counts(info_dataframe['Population']).iloc[:10].index)
        pop_count_plot.set_xticklabels(pop_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')
    if ('Bin' in axis_dict):
        pop_count_plot = sns.countplot(ax=axes[axis_dict['Bin']],x="Bin", data=info_dataframe, order=pd.value_counts(info_dataframe['Bin']).iloc[:10].index)
        pop_count_plot.set_xticklabels(pop_count_plot.get_xticklabels(), rotation=30, horizontalalignment='right')

    composite_plot.savefig(output_figure_file)
    plt.close()
    
    if (og_table_out_file != 'NA' ):
        og_dataframe = index_info(og_table_out_file,'Sequence')
        filtered_og_dataframe = og_dataframe[og_dataframe.columns[og_dataframe.sum()>3]]
        (ideal_height,ideal_width) = filtered_og_dataframe.shape
        figure, ax = plt.subplots(figsize=(ideal_width/20,ideal_height/20)) 
        og_heatmap_plot = sns.heatmap(filtered_og_dataframe,ax=ax,xticklabels=False,center=1,cmap="viridis") 
        figure.savefig(f'Heatmap_{prefix_genome_file}_OG_Count.png')
    
    if (og_score_table_out_file != 'NA' ):
        og_score_dataframe = index_info(og_score_table_out_file,'Sequence')
        filtered_og_score_dataframe = og_score_dataframe
        (ideal_height,ideal_width) = filtered_og_score_dataframe.shape
        figure, ax = plt.subplots(figsize=(ideal_width/20,ideal_height/20)) 
        og_heatmap_plot = sns.heatmap(filtered_og_score_dataframe,ax=ax,xticklabels=False,cmap="viridis") 
        figure.savefig(f'Heatmap_{prefix_genome_file}_OG_Score.png')
        
#2D dictionary to store all relevant information about sequences
seq_info = defaultdict(dict)
#Global variables to be used by multiple modules
merged_genomes_file = 'All_Genomic.fasta'
merged_genes_file = 'All_Genes.fasta'
merged_cds_file = 'All_CDS.faa'
#Central module to run all other modules
central()
