<p align="center">
  <img src="https://github.com/felipehcoutinho/virathon/blob/main/Virathon_Logo.png" width="400" height="400" alt="Virathon logo generated with DALLE"/>
</p>

# Virathon: Genomic Analysis of Viruses of Archaea and Bacteria

## Introduction

Virathon is designed to automate the analysis of genomic sequences derived from viruses of Archaea and Bacteria, specially uncultured ones originated from metagenomic samples

***

## Dependencies
Virathon is writen in Python 3 and uses multiple external depencies.

- [Bowtie2](https://sourceforge.net/projects/bowtie-bio/files/bowtie2/2.4.2/)
- [CheckV](https://bitbucket.org/berkeleylab/checkv/src/master/)
- [Hmmer](https://github.com/EddyRivasLab/hmmer)
- [MetaBat2](https://bitbucket.org/berkeleylab/metabat/src/master/)
- [MMSeqs2](https://github.com/soedinglab/MMseqs2)
- [NCBI BLAST+](https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastDocs&DOC_TYPE=Download)
- [Prodigal](https://github.com/hyattpd/Prodigal)
- [RaFAH](https://sourceforge.net/projects/rafah/)
- [PHIST](https://github.com/refresh-bio/PHIST)
- [Samtools](http://www.htslib.org/)
- [SPAdes](https://github.com/ablab/spades)
- [VIBRANT](https://github.com/AnantharamanLab/VIBRANT)
- [VirHostMatcher-Net](https://github.com/WeiliWw/VirHostMatcher-Net)
- [vpf-class](https://github.com/biocom-uib/vpf-tools)

***

## Commands

### Assembling (or co-assembling) genomes, metagenomes, or viromes with SPAdes:
`python3 Virathon.py --assemble True --raw_read_table Metagenome_Info.tsv --threads 24`

The raw_read_table is a tsv format table with 4 columns with exactly thse headers: Sample R1 R2 Group. Where Sample defines the unique identifier to be used for a sample read pair (e.g. genome, metagenome, SAG sequencing). R1 and R2 define the full path of the R1 and R2 file sin your system. Group definies in which group the sample should co-assembled. Samples in the same group are co-assembled. Specifying a unique group for each samples results in samples being assembled individually. The value of Group column is also used to name the output directory and to rename the assembled scaffolds.

### Indexing basic sequence information
Passing genomic, gene, or cds files will prompt virathon to collect basic information for genomic sequences (sequence ID, description, length, GC content, number oc CDS and genes epr scaffold) and print it to the Seq_Info.tsv file. Multiple genome, cds, or gene files may be provided at a time. Generated files:

### Indexing a single genomicfile
`python3 Virathon.py --genome_files My_Genomes.fasta`

### Indexing a genomic, a cds, and a gene sequence file
`python3 Virathon.py --genome_files My_Genomes.fasta --cds_files My_CDS.faa --gene_files My_Genes.fna`
- All_Genomic.fasta (If at least one genomic sequence file is provided to --genome_files)
- All_CDS.fasta (If at least one CDS sequence file is provided to --cds_files)
- All_Genes.fasta (If at least one gene sequence file is provided to --cds_files)
- Seq_Info.tsv

### Indexing three genomic, no cds, and a single gene sequence file, and writing the output table to  Info_Genomes.tsv
`python3 Virathon.py --genome_files My_Genomes_1.fasta My_Genomes_2.fasta My_Genomes_3.fasta --gene_files My_Genes_1+2+3.fna --info_output Info_Genomes.tsv`

### Clustering viral genomic sequences into viral populations (VPs) starting from a single file of genomic sequences
`python3 Virathon.py --genome_files My_Genomes.fasta --make_pops True --threads 24 `
This will generate the following files:
- Seq_Info.tsv, in which the Population column idicates the VP to which the sequence was assigned, while the Population_Representative indicates if said sequence is the Representative of the VP (i.e. longest sequence)
Note: If --gene_files is not provided, will call genes with Prodigal.

### Clustering viral genomic sequences into viral populations (VPs) starting from a single file of genomic sequences and a single genes file containing the DNA sequences of all genes derived from all the genomic sequences
`python3 Virathon.py --genome_files My_Genomes.fasta --make_pops True --threads 24 --gene_files My_Genes.fna`
Note: Genomic sequences always needs to be provided even if the genes are provided as well
 
###	Generating an Orthologous Group (OG) count x Genome table starting from a fasta file of genomic sequences
`python3 Virathon.py --genome_files My_Genomes.fasta --call_ogtable_module True`

This will generate the following files:
-  OG_Count_Table_My_Genomes.tsv in which rows represent genomic sequences, columns represent orthologous groups, and cells are filled with the count of proteins derived from each genomic sequence in each orthologous group

###	Generating an Orthologous Group (OG) phylogenies starting from a fasta file of genomic sequences and using only OGs with at least 5 proteins
`python3 Virathon.py --genome_files My_Genomes.fasta --og_phylogeny True --min_cluster_size 5`

This will generate the following files:
-  OG_Count_Table_My_Genomes.tsv in which rows represent genomic sequences, columns represent orthologous groups, and cells are filled with the count of proteins derived from each genomic sequence in each orthologous group
-  Unaligned_Clusters_My_Genomes directory containing multiple fasta files, each containing the unaligned sequences according to their OG assignment, provided that the OG has at least 5 proteins
-  Aligned_Clusters_My_Genomes directory containing multiple fasta files, each containing the aligned (using Muscle) sequences from each OG, provided that the OG has at least 5 proteins
-  Phylogenies_Aligned_Clusters_My_Genomes directory containing multiple fasta files, each containing the aligned (using Muscle) sequences from each OG, provided that the OG has at least 5 proteins 

### Calculating abundances by read mapping staring from a fasta file of genomic sequences
`python3 Virathon.py --genome_files My_Genomes.fasta --abundance_table True --abundance_rpkm True --raw_read_table Metagenome_Info.tsv --threads 24`

### Calculating abundances by read mapping staring from a directory containing multiple fasta files of genomic sequences
`python3 Virathon.py --genome_files My_Genomes/*.fasta --abundance_table True --abundance_rpkm True --raw_read_table Metagenome_Info.tsv --threads 24`

### Calculating abundances by read mapping staring from a Bowtie2 database
`python3 Virathon.py --bowtiedb My_DB_Prefix --abundance_table True --abundance_rpkm True --raw_read_table Metagenome_Info.tsv --threads 24`

### Running host prediction and taxonomic assignment with vpf-class:
`python3 Virathon.py --genome_files My_Genomes.fasta --call_vpf_class True`

This will generate the following files:
-  VPF_Class_My_Genomes directory containing: baltimore.tsv  family.tsv  genus.tsv  host_domain.tsv  host_family.tsv  host_genus.tsv

### Running host predictions with PHIST starting from putative host and viral genomes in fasta files:
Note: Host genomes should always be provided as the directory containing multifasta files. Viral genomes can be provided in a single fasta file containing all sequences, or as multiple fasta files. Regardles of the choice, predictions are reported at the individual viral sequence level x host genome file level.

`python3 Virathon.py --phist_host_prediction True --genome My_Genomes.fasta --putative_host_genomes_directory /my/host/genomes/dir/ --extension_putative_host_genomes fasta`

Note: In case the host genomes might be contaminated with viral sequences which are 100% identical to the query sequences the --remove_exact_mathces flag must be set to True.

`python3 Virathon.py --phist_host_prediction True --genome My_Genomes.fasta --putative_host_genomes_directory /my/host/genomes/dir/ --extension_putative_host_genomes fasta --remove_exact_matches True`

### Running host predictions with RaFAH starting from a genomes fasta file:
`python3 Virathon.py --call_rafah True --genome My_Genomes.fasta`

This will generate the following files:
- My_Genomes.faa
- My_Genomes.fna
- My_Genomes.gff
- RaFAH_My_Genomes_Seq_Info_Prediction.tsv
- RaFAH_My_Genomes_Host_Predictions.tsv
- RaFAH_My_Genomes_Genome_to_OG_Score_Min_Score_50-Max_evalue_1e-05_Prediction.tsv
- RaFAH_My_Genomes_CDSxClusters_Prediction

### Running host predictions with RaFAH starting from a CDS fasta file:
`python3 Virathon.py --call_rafah True --cds My_CDS.faa`

This will generate the following files:
- RaFAH_My_Genomes_Seq_Info_Prediction.tsv
- RaFAH_My_Genomes_Host_Predictions.tsv
- RaFAH_My_Genomes_Genome_to_OG_Score_Min_Score_50-Max_evalue_1e-05_Prediction.tsv
- RaFAH_My_Genomes_CDSxClusters_Prediction

### Querying a protein file in fasta format against a hmmer formatted database using hmmsearch:
`python3 Virathon.py --call_hmmer True --cds My_CDS.faa --hmmer_program hmmsearch --hmmer_db My_Hmmer_DB.hmm`

This will generate the following files:
- My_CDSxMy_Hmmer_DB.hmmsearch

### Querying a protein file in fasta format against a hmmer formatted database using hmmscan:
`python3 Virathon.py --call_hmmer True --cds My_CDS.faa --hmmer_program hmmsscan --hmmer_db My_Hmmer_DB.hmm`

This will generate the following files:
- My_CDSxMy_Hmmer_DB.hmmscan
