# Virathon: Genomic Analysis of Viruses of Archaea and Bacteria

## Introduction

Virathon is designed to automate the analysis of the genomes of viruses of Archaea and Bacteria, specially uncultured ones originated from metagenomic samples

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
- [Samtools](http://www.htslib.org/)
- [SPAdes](https://github.com/ablab/spades)
- [VIBRANT](https://github.com/AnantharamanLab/VIBRANT)
- [VirHostMatcher-Net](https://github.com/WeiliWw/VirHostMatcher-Net)
- [vpf-class](https://github.com/biocom-uib/vpf-tools)

***

## Commands
### Running host prediction and taxonomic assignment with vpf-class:
`python3 virathon_v0.1.py --genome_files My_Genomes.fasta --call_vpf_class True`

This will generate the following files:
-  VPF_Class_My_Genomes directory containing: baltimore.tsv  family.tsv  genus.tsv  host_domain.tsv  host_family.tsv  host_genus.tsv

### Running host predictions with RaFAH starting from a genomes fasta file:
`python3 virathon_v0.1.py --call_rafah True --genome My_Genomes.fasta`

This will generate the following files:
- My_Genomes.faa
- My_Genomes.fna
- My_Genomes.gff
- RaFAH_My_Genomes_Seq_Info_Prediction.tsv
- RaFAH_My_Genomes_Host_Predictions.tsv
- RaFAH_My_Genomes_Genome_to_OG_Score_Min_Score_50-Max_evalue_1e-05_Prediction.tsv
- RaFAH_My_Genomes_CDSxClusters_Prediction

### Running host predictions with RaFAH starting from a CDS fasta file:
`python3 virathon_v0.1.py --call_rafah True --cds My_CDS.faa`

This will generate the following files:
- RaFAH_My_Genomes_Seq_Info_Prediction.tsv
- RaFAH_My_Genomes_Host_Predictions.tsv
- RaFAH_My_Genomes_Genome_to_OG_Score_Min_Score_50-Max_evalue_1e-05_Prediction.tsv
- RaFAH_My_Genomes_CDSxClusters_Prediction

### Querying a protein file in fasta format against a hmmer formatted database using hmmsearch:
`python3 virathon_v0.1.py --call_hmmer True --cds My_CDS.faa --hmmer_program hmmsearch --hmmer_db My_Hmmer_DB.hmm`

This will generate the following files:
- My_CDSxMy_Hmmer_DB.hmmsearch

### Querying a protein file in fasta format against a hmmer formatted database using hmmscan:
`python3 virathon_v0.1.py --call_hmmer True --cds My_CDS.faa --hmmer_program hmmsscan --hmmer_db My_Hmmer_DB.hmm`

This will generate the following files:
- My_CDSxMy_Hmmer_DB.hmmscan
