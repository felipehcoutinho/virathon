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
- [Samtools](http://www.htslib.org/)
- [SPAdes](https://github.com/ablab/spades)
- [VIBRANT](https://github.com/AnantharamanLab/VIBRANT)
- [VirHostMatcher-Net](https://github.com/WeiliWw/VirHostMatcher-Net)

***

## Commands
### Querying a protein file in fasta format against a hmmer formateed database using hmmsearch:
`python3 virathon_v0.1.py --call_hmmer True --cds My_CDS.faa --hmmer_program hmmsearch --hmmer_db My_Hmmer_DB.hmm`
This will generate the following files:
- My_CDSxMy_Hmmer_DB.hmmsearch

### Querying a protein file in fasta format against a hmmer formateed database using hmmscan:
`python3 virathon_v0.1.py --call_hmmer True --cds My_CDS.faa --hmmer_program hmmsscan --hmmer_db My_Hmmer_DB.hmm`
This will generate the following files:
- My_CDSxMy_Hmmer_DB.hmmscan
