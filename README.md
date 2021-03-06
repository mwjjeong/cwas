# Category-wide association study (CWAS) (An et al. 2018)

*Note: This is a modified version of the original CWAS repository.*
*The original CWAS repository: [sanderslab/cwas](https://github.com/sanderslab/cwas)*

## Data requirements
Users must prepare following data for CWAS because it is very essential but cannot be generated automatically. Here are details.

### 1. Input VCF data (De novo variant list)
```
#CHROM  POS ID  REF ALT QUAL    FILTER  INFO
chr1    3747728 .        T       C       .       .       SAMPLE=11000.p1;BATCH=P231
chr1    38338861        .       C       A       .       .       SAMPLE=11000.p1;BATCH=P231
chr1    117942118       .      T       G       .       .       SAMPLE=11000.p1;BATCH=P231
```
- The input VCF data must follow the [specification of VCF](https://samtools.github.io/hts-specs/VCFv4.2.pdf).
- The *INFO* field must contain a sample ID of each variant with this format `SAMPLE={sample_id}`. 

### 2. List of samples
| SAMPLE | FAMILY | PHENOTYPE |
|:---:|:---:|:---:|
| 11000.p1 | 11000 | case |
| 11000.s1 | 11000 | ctrl |
| 11002.p1 | 11002 | case |
| 11002.s1 | 11002 | ctrl |
- CWAS requires the file like above listing sample IDs with its family IDs and phenotypes (Case=*case*,  Control=*ctrl*).
- Here are details of the required format.
    - Tab separated
    - 3 essential columns: *SAMPLE*, *FAMILY*, and *PHENOTYPE*
    - A value in the *PHENOTYPE* must be *case* or *ctrl*.
- The values in the *SAMPLE* must be matched with the sample IDs of variants in the input VCF file.
- *Note*: Currently, There is an assumption that the samples are from quadruple families.

### 3. List of adjustment factors (Optional)
| SAMPLE | AdjustFactor |
|:---:|:---:|
| 11000.p1 | 0.932 |
| 11000.s1 | 1.082 |
| 11002.p1 | 0.895 |
| 11002.s1 | 1.113 |
- The file like above is required if you want to adjust the number of variants for each sample in CWAS.
- Here are details of the required format.
    - Tab separated
    - 2 essential columns: *SAMPLE* and *AdjustFactor*
    - A value in the *AdjustFactor* must be a float.
- The values in the *SAMPLE* must be matched with the sample IDs of variants in the input VCF file.


## Data Preparation
Following steps purpose to generate required data by downloading and processing publicly available data.

### Step 1. Download data
Following data will be downloaded.
- List of low-complexity regions of human genome
- List of gap regions of human genome
- Information of each chromosome (its sequence and size)

##### Script:
`download.py`

##### Optional arguments:
- -f, --force_overwrite = If it is specified, it is forced to download data regardless of existence of the data.

```bash
# Help
./download.py -h

# Usage
./download.py [-f]

# Note: '[]' means they are optional arguments. 
```

### Step 2. Generate required data
This step includes
- Data preparation for *random mutation simulation*
    - Sort the list of gap regions
    - Generate a list of regions that should be masked in the human genome
    - Mask each chromosome sequence
- Data preparation for *variant annotation*
    - Filtering coordinates of BED file from Yale
    - Merge annotation information of BED files for custom annotations.

##### Script:
`prepare.py`

##### Optional arguments:
- -f, --force_overwrite = If it is specified, it is forced to generate data regardless of existence of the data.
- -p, --num_proc = Number of processes for this script. Default is *1*.

```bash
# Preparation for simulating random mutations
# Help
./prepare.py simulation -h

# Usage
./prepare.py simulation \
[-f] \
[-p NUM_PROC]


# Preparation for variant annotation
# Help
./prepare.py annotation -h

# Usage
./prepare.py annotation \
[-f] \
[-p NUM_PROC]

# Note: '[]' means they are optional arguments. 
```

### Step 3. Random mutation simulation (Optional)
If users want, users can generate lists of random mutations as a VCF format via this step. This simulation can be used to get simulated p-values for CWAS.

##### Script:
`simulate.py`

##### Prerequisite:
- Run **Step 2** in **Data Preparation** (Data preparation for *simulation*).

##### Required arguments:
- -i, --in_vcf_path = Path to file listing variants (VCF format), which format is described in **Data requirments** above. A distribution of generated random mutation types will follow the distribution of variant types in this VCF.
- -s, --sample_file = Path to a file listing sample IDs, which format is described in **Data requirments** above.

##### Optional arguments:
- -o, --out_dir = Directory of generated VCFs that list random mutations. Default is *./random-mutation*.
- -t, --out_tag = Prefix of the generated VCFs. Each VCF filename will start with this tag. Default is *rand_mut*.
- -n, --num_sim = Number of simulations. The number of generated VCFs will be same with the number of simulations.
- -p, --num_proc = Number of processes for this script. Default is *1*.
   
##### Generated VCF path:
`{out_dir}/{out_tag}.{simultation index [1, num_sim]}.vcf`

```bash
# Help
./simulate.py -h

# Usage
./simulate.py \
-i IN_VCF_PATH \
-s SAMPLE_FILE_PATH \
[-o OUT_DIR] \
[-t OUT_TAG] \
[-n NUM_SIM] \
[-p NUM_PROC]

# Note: '[]' means they are optional arguments. 
```
 
## CWAS Execution
### Step 1. Variant annotation
This step purposes to annotate user-provided de novo variants. In this step, the variants is annotated for genomic regions, conservation scores, functional regions including user-defined functional regions. *Variant Effect Predictor* (VEP; https://www.ensembl.org/vep) is used to annotate genomic regions and conservation scores.

##### Script: 
`annotate.py`

##### Prerequisite:
- Run **Step 2** in **Data Preparation** (Data preparation for *annotation*).

##### Required arguments:
- -i, --in_vcf_path = Path to file listing variants (VCF format), which format is described in **Data requirments** above.


##### Optional arguments:
- -o, --out_vcf_path = Path to the VEP result (VCF format). Default path is *annotate_output.vcf*.
- -s, --split_vcf = If 1, split the input VCF by chromosome, run VEP for each split VCF, and concatenate them. Default is *0*.
- -p, --num_proc = Number of processes for this script (only necessary for the split VCF files). Default is *1*.
- --vep = Path of a Perl script to execute VEP. As a default, VEP already installed via *pip* or *conda* will be used.

```bash
# Help
./annotate.py -h

# Usage
./run_vep.py \
-i IN_VCF_PATH \
[-o OUT_VCF_PATH]  \
[-s {0, 1}] \
[-p NUM_PROC] \
[--vep VEP_SCRIPT]

# Note: '[]' means they are optional arguments. '{}' contains possible values for the argument. 
```

### Step 2. Variant categorization
The annotated variants will be grouped by annotation categories (or CWAS categories) and individuals (or samples). 

##### Script: 
`categorize.py`

##### Prerequisite:
- Run **Step 1. Variant annotation** in **CWAS Execution**.

##### Requirement: 
Cython (http://cython.org/). Please note that this script will use Cython. So you need to compile a Cython script (`categorization.pyx`) to run run.

##### Required arguments:
- -i, --infile = Path to file listing variants annotated by VEP, which is an output of `run_vep.py` (**Step 1**). 

##### Optional arguments:
- -o, --outfile = Path to the categorization result. Default path is *cwas_cat_result.txt*.
- -p, --num_proc = Number of processes for this script. Default is *1*.
- -a, --af_known = Keep the variants with known allele frequencies by gnomAD. Possible values are *{yes, no, only}*. Default is *yes*.

```bash
# Help
./categorize -h

# Usage
./categorize.py \
-i IN_VCF_PATH \
[-o OUTFILE_PATH]  \
[-p NUM_PROC] \
[-a {yes, no, only}]

# Note: '[]' means they are optional arguments. '{}' contains possible values for the argument. 
```

### Step 3-1. Burden tests on the CWAS categories
Each category from the step 2 will be subject to burden tests using binomial tests or permutation tests on total variant counts per category between cases and unaffected controls. 

##### Script: 
`burden_test.py`

##### Prerequisite:
- Run **Step 2. Variant categorization** in **CWAS Execution**.

##### Required arguments:
- -i, --infile = Path to a result of the categorization, which is an output `categorize.py` (**Step 2**).
- -s, --sample_file = Path to a file listing sample IDs, which format is described in **Data requirments** above.

##### Optional arguments:
- -a, --adj_file = Path to a file specifying adjustment factors the the number of variants of each individual, which format is described in **Data requirments** above. Default is *'' (empty string)*, which will bypass this adjustment step.
- -o, --outfile = Path to a result of the burden tests. Default is *cwas_burden_binom_result.txt* if you have excuted binomial tests, or *cwas_burden_perm_result.txt* if you have excuted permutation tests.

##### Optional arguments *only for permutation tests*:
- -n, --num_perm = Number of label-swapping permutations. Default is *10,000*.
- -p, --num_proc = Number of processes for this script. Default is *1*.
- -po, --perm_outfile = Path to a file listing relative risks after permutations for each category. Default is *'' (empty string)*, which will not save the relative risks after permutations.


```bash
# For binomial tests
# Help
./burden_test.py binom -h

# Usage
./burden_test.py binom \
-i CAT_RESULT_PATH \
-s SAMPLE_FILE_PATH \ 
[-a ADJ_FILE_PATH] \
[-o OUTFILE_PATH]


# For permutation tests
# Help
./burden_test.py perm -h

# Usage
./burden_test.py perm \
-i CAT_RESULT_PATH \
-s SAMPLE_FILE_PATH \ 
[-a ADJ_FILE_PATH] \
[-o OUTFILE_PATH] \
[-n NUM_PERM] \
[-p NUM_PROC] \
[-po PERM_RR_PATH]

# Note: '[]' means they are optional arguments.
```

### Step 3-2. De novo risk score analysis 
This step does a lasso regression to determine which categories are possible deterministic factors for the phenotypes. Each category from the step 2 will be subject to this analysis.

##### Script
`risk_score.py`

##### Prerequisite:
- Run **Step 2. Variant categorization** in **CWAS Execution**.

##### Requirement
- A python package *glmnet* ([civisanalytics/python-glmnet](https://github.com/civisanalytics/python-glmnet)) must be installed for a lasso regression. Use the following commands to install.

##### Required arguments:

- -i, --infile = Path to a result of the categorization, which is an output `categorize.py` (**Step 2**).
- -s, --sample_file = Path to a file listing sample IDs, which format is described in **Data requirments** above.

##### Optional arguments:

- -a, --adj_file = Path to a file specifying adjustment factors the the number of variants of each individual, which format is described in **Data requirments** above. Default is *'' (empty string)*, which will bypass this adjustment step.
- -o, --outfile = Path to a result of the risk score analysis. Default is *cwas_denovo_risk_score_result.txt*.
- --category_group = Group of the CWAS categories for this analysis. Current possible values are *{all, coding, coding-no-ptv, noncoding, promoter, noncoding-wo-promoter}*. Default is *all*.
- --rare_category_cutoff = Rare category cutoff for the number of variants in controls. Default is 3.
- --train_set_fraction = Fraction of the training set. Default is *0.3*.
- --num_regression = The number of regression trials. Default is *10*.
- --num_cv_fold = The number of cross-validation folds. Default is *5*.
- --use_parallel = Boolean value to determine whether or not to use multiprocessing for cross-validation. Possible values are *{0, 1}*. Default is *1*.
- --do_test = Boolean value to determine whether or not to do permutation tests to get a p-value for the R square. Possible values are *{0, 1}*. Default is *0*.
- --num_perm = The number of label-swapping permutations. Default is *1,000*.

All the default values are consistent with *An et al., Science, 2018*.


```bash
# Help
./risk_score.py -h

# Usage
./risk_score.py \
-i CAT_RESULT_PATH \
-s SAMPLE_FILE_PATH \ 
[-a ADJ_FILE_PATH] \
[-o OUTFILE_PATH] \
[--category_group {all,coding,coding-no-ptv,noncoding,promoter,noncoding-wo-promoter}] \
[--rare_category_cutoff RARE_CAT_CUTOFF] \
[--train_set_fraction TRAIN_SET_F] \
[--num_regression NUM_REG] \
[--num_cv_fold NUM_CV_FOLD] \
[--use_parallel {0,1}] \
[--do_test {0,1}] \
[--num_perm NUM_PERM]

# Note: '[]' means they are optional arguments.
```

**The steps below are not implemented yet.**
***

### Step 4. Run burdenshift

This script will generate global burdenshift cross a large category (e.g. promoters, missenses). This is based on permutation files generated from the step 3. 

##### Script: 
`run_burdenShift.R`

```
Rscript  \
run_burdenShift.R \
result.perm_p.cwas.txt.gz \ # Permutation p-value matrix from the Step 5.
result.perm_burdenshift.cwas.txt.gz \ # Burden matrix from the Step 4.
list_catSetMembership.txt \ # Matrix for a large category membership
10000 \ # Number of permutation used in the Step 5.
0.05 \ # p-value threshold
cwas  # Tag for output
```
