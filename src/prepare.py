#!/usr/bin/env python
"""
Script for data preparation for category-wide association study (CWAS)
"""
import argparse
import os
import yaml
import gzip

from collections import defaultdict

from utils import get_curr_time


def main():
    # Paths for this script
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(curr_dir)
    ori_file_conf_path = os.path.join(project_dir, 'conf', 'download_filepaths.yaml')  # Files downloaded already
    target_file_conf_path = os.path.join(project_dir, 'conf', 'prepare_filepaths.yaml')  # Files that will be made

    # Parse the configuration files
    with open(ori_file_conf_path) as ori_file_conf_file, open(target_file_conf_path) as target_file_conf_file:
        ori_filepath_dict = yaml.safe_load(ori_file_conf_file)
        target_filepath_dict = yaml.safe_load(target_file_conf_file)

        for file_group in target_filepath_dict:
            for file_key in target_filepath_dict[file_group]:
                ori_filepath_dict[file_group][file_group] = \
                    os.path.join(project_dir, ori_filepath_dict[file_group][file_key])
                target_filepath_dict[file_group][file_group] = \
                    os.path.join(project_dir, target_filepath_dict[file_group][file_key])

    # Parse arguments
    parser = create_arg_parser()
    args = parser.parse_args()

    if args.step == 'simulate':
        print(f'[{get_curr_time()}, Progress] Prepare data for random mutation simulation')
        make_mask_region_bed(ori_filepath_dict, target_filepath_dict)
        mask_fasta(ori_filepath_dict, target_filepath_dict)
        make_chrom_size_txt(target_filepath_dict)

    print(f'[{get_curr_time()}, Progress] Done')


def create_arg_parser() -> argparse.ArgumentParser:
    """ Create an argument parser for this script and return it """
    # Create a top-level argument parser
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(description='Step for which data is prepared', dest='step')
    subparsers.add_parser('simulate', description='Prepare data to simulate random mutations',
                          help='Prepare data to simulate random mutations (arg "simulate -h" for usage)')
    return parser


def make_mask_region_bed(ori_filepath_dict: dict, target_filepath_dict: dict):
    """ Make a bed file listing masked regions by merging gap and LCR regions """
    gap_path = ori_filepath_dict['gap']
    lcr_path = ori_filepath_dict['lcr']
    sort_gap_path = target_filepath_dict['gap']
    mask_region_path = target_filepath_dict['mask_region']

    if not os.path.isfile(sort_gap_path):
        cmd = f'gunzip -c {gap_path} | cut -f2,3,4 - | sort -k1,1 -k2,2n | gzip > {sort_gap_path};'
        print(f'[{get_curr_time()}, Progress] Sort the gap regions')
        os.system(cmd)

    if not os.path.isfile(mask_region_path):
        cmd = f'zcat {sort_gap_path} {lcr_path} | sortBed -i stdin | gzip > {mask_region_path}'
        print(f'[{get_curr_time()}, Progress] Merge the gap and LCR regions')
        os.system(cmd)


def mask_fasta(ori_filepath_dict: dict, target_filepath_dict: dict):
    """ Mask regions on the genome files (FASTA files) and save results as new FASTA files """
    mask_region_path = target_filepath_dict['mask_region']
    chroms = [f'chr{n}' for n in range(1, 23)]

    for chrom in chroms:
        in_fa_gz_path = ori_filepath_dict[chrom]
        in_fa_path = in_fa_gz_path.replace('.gz', '')
        out_fa_path = target_filepath_dict[chrom]

        if not os.path.isfile(out_fa_path):
            print(f'[{get_curr_time()}, Progress] Mask the {chrom} fasta file and index the output')
            cmd = f'gunzip {in_fa_gz_path};'
            cmd += f'maskFastaFromBed -fi {in_fa_path} -fo {out_fa_path} -bed {mask_region_path};'
            cmd += f'samtools faidx {out_fa_path};'
            os.system(cmd)


def make_chrom_size_txt(target_filepath_dict: dict):
    """ Make a txt file listing total size, mapped, AT/GC, and effective sizes of each chromosome """
    chrom_size_path = target_filepath_dict['chrom_size']
    chroms = [f'chr{n}' for n in range(1, 23)]

    if not os.path.isfile(chrom_size_path):
        print(f'[{get_curr_time()}, Progress] Make a file listing total, mapped, AT/GC, and effective sizes '
              f'of each chromosome')

        with open(chrom_size_path, 'w') as outfile:
            print('Chrom', 'Size', 'Mapped', 'AT', 'GC', 'Effective', sep='\t', file=outfile)

            for chrom in chroms:
                print(f'[{get_curr_time()}, Progress] {chrom}')
                mask_fa_path = target_filepath_dict[f'{chrom}']
                fa_idx_path = mask_fa_path + '.fai'

                with open(fa_idx_path) as fa_idx_file:
                    line = fa_idx_file.read()
                    fields = line.split('\t')
                    chrom_size = int(fields[1])
                    base_start_idx = int(fields[2])

                with gzip.open(mask_fa_path, 'rt') as mask_fa_file:
                    base_cnt_dict = defaultdict(int)
                    mask_fa_file.seek(base_start_idx)
                    seq = mask_fa_file.read()

                    for base in seq:
                        base_cnt_dict[base.upper()] += 1

                map_size = chrom_size - base_cnt_dict['N']
                at_size = base_cnt_dict['A'] + base_cnt_dict['T']
                gc_size = base_cnt_dict['G'] + base_cnt_dict['C']
                effect_size = (at_size / 1.75) + gc_size
                print(chrom, chrom_size, map_size, at_size, gc_size, effect_size, sep='\t', file=outfile)


if __name__ == '__main__':
    main()