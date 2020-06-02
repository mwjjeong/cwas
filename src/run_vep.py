#!/usr/bin/env python
"""
Script for genomic and functional annotations using VEP.
"""

import argparse
import multiprocessing as mp
import os

import yaml


def main():
    # Paths to essential configuration files
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(curr_dir)
    vep_custom_data_dir = os.path.join(project_dir, 'data', 'vep')
    vep_custom_conf_path = os.path.join(project_dir, 'conf', 'vep_custom_annotations.yaml')

    # Parse the configuration file
    with open(vep_custom_conf_path) as vep_custom_conf:
        custom_filename_dict = yaml.safe_load(vep_custom_conf)

    # Create and parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--infile', dest='in_vcf_path', required=True, type=str, help='Input VCF file')
    parser.add_argument('-o', '--outfile', dest='out_vcf_path', required=False, type=str,
                        help='Path of the VCF output', default='vep_output.vcf')
    parser.add_argument('-p', '--num_proc', dest='num_proc', required=False, type=int,
                        help='Number of processes for this script', default=1)
    args = parser.parse_args()

    # Check the validity of the arguments
    assert os.path.isfile(args.in_vcf_path), f'The input VCF file "{args.in_vcf_path}" cannot be found.'
    outfile_dir = os.path.dirname(args.out_vcf_path)
    assert outfile_dir == '' or os.path.isdir(outfile_dir), f'The outfile directory "{outfile_dir}" cannot be found.'
    assert 1 <= args.num_proc <= mp.cpu_count(), \
        f'Invalid number of processes "{args.num_proc:,d}". It must be in the range [1, {mp.cpu_count()}].'

    # Print the settings (arguments)
    print(f'[Setting] The input VCF file: {args.in_vcf_path}')  # VCF from VEP
    print(f'[Setting] The output path: {args.out_vcf_path}')
    print(f'[Setting] No. processes for this script: {args.num_proc:,d}')
    print()

    # Split the input file for a single chromosome
    chrom_to_file = {}
    vcf_file_paths = []

    with open(args.in_vcf_path) as in_vcf_file:
        header = in_vcf_file.readline()

        for line in in_vcf_file:
            chrom = line.split('\t')[0]
            chr_vcf_file = chrom_to_file.get(chrom)

            if chr_vcf_file is None:
                chr_vcf_file_path = args.in_vcf_path.replace('.vcf', f'.tmp.{chrom}.vcf')
                vcf_file_paths.append(chr_vcf_file_path)
                chr_vcf_file = open(chr_vcf_file_path, 'w')
                chr_vcf_file.write(header)
                chrom_to_file[chrom] = chr_vcf_file

            chr_vcf_file.write(line)

    for chr_vcf_file in chrom_to_file.values():
        chr_vcf_file.close()

    # Make commands for VEP
    cmds = []
    vep_out_file_paths = []

    for vcf_file_path in vcf_file_paths:
        out_file_path = vcf_file_path.replace('.vcf', '.vep.vcf')
        vep_out_file_paths.append(out_file_path)

        # Basic information
        cmd_args = [
            'vep',
            '--assembly', 'GRCh38',
            '--cache',
            '--force_overwrite',
            '--format', 'vcf',
            '-i', vcf_file_path,
            '-o', out_file_path,
            '--vcf',
            '--no_stats',
            '--polyphen p',
        ]

        # Only the most severe consequence per gene.
        cmd_args += [
            '--per_gene',
            '--pick',
            '--pick_order', 'canonical,appris,tsl,biotype,ccds,rank,length',
        ]

        # Add options for nearest and distance
        cmd_args += [
            '--distance', '2000',
            '--nearest', 'symbol',
            '--symbol',
        ]

        # Add custom annotations
        for custom_annot in custom_filename_dict:
            custom_filename = custom_filename_dict[custom_annot]
            custom_file_path = os.path.join(vep_custom_data_dir, custom_filename)

            if custom_file_path.endswith('vcf') or custom_file_path.endswith('vcf.gz'):
                cmd_args += [
                    '--custom',
                    ','.join([custom_file_path, custom_annot, 'vcf', 'exact', '0', 'AF']),
                ]
            elif custom_file_path.endswith('bw') or custom_file_path.endswith('bw.gz'):
                cmd_args += [
                    '--custom',
                    ','.join([custom_file_path, custom_annot, 'bigwig', 'overlap', '0']),
                ]
            else:  # BED files (.bed or .bed.gz)
                cmd_args += [
                    '--custom',
                    ','.join([custom_file_path, custom_annot, 'bed', 'overlap', '0']),
                ]

        cmd = ' '.join(cmd_args)
        cmds.append(cmd)

    # Run VEP in parallel
    pool = mp.Pool(args.num_proc)
    pool.map(os.system, cmds)
    pool.close()
    pool.join()

    # Collates the VEP outputs into one
    with open(args.out_vcf_path, 'w') as outfile:
        for i, vep_out_file_path in enumerate(vep_out_file_paths):
            with open(vep_out_file_path) as vep_outfile:
                if i == 0:  # Write all lines from the file
                    for line in vep_outfile:
                        outfile.write(line)
                else:  # Write all lines except headers
                    for line in vep_outfile:
                        if not line.startswith('#'):
                            outfile.write(line)

    # Delete the temporary files
    for vcf_file_path in vcf_file_paths:
        os.remove(vcf_file_path)

    for vep_out_file_path in vep_out_file_paths:
        os.remove(vep_out_file_path)


if __name__ == "__main__":
    main()
