#!/usr/bin/python
# File created on 09 Feb 2010
from __future__ import division

__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2011, The QIIME Project"
__credits__ = ["Greg Caporaso"]
__license__ = "GPL"
__version__ = "1.4.0"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"
__status__ = "Release"
 

from qiime.util import parse_command_line_parameters
from qiime.util import make_option
from os import popen, system, mkdir, makedirs
from os.path import split, splitext, join
from subprocess import check_call, CalledProcessError
from qiime.util import get_tmp_filename
from qiime.parallel.util import (split_fasta, get_random_job_prefix, write_jobs_file,
    submit_jobs, compute_seqs_per_file, build_filepaths_from_filepaths,
    get_poller_command, write_filepaths_to_file,
    write_merge_map_file_assign_taxonomy, merge_to_n_commands)
from qiime.util import get_qiime_scripts_dir, get_options_lookup
from qiime.parallel.multiple_rarefactions import get_job_commands

options_lookup = get_options_lookup()

script_info={}
script_info['brief_description']="""Parallel multiple file rarefaction"""
script_info['script_description']="""This script performs like the multiple_rarefactions.py script, but is intended to make use of multicore/multiprocessor environments to perform analyses in parallel."""
script_info['script_usage']=[]
script_info['script_usage'].append(("""Example""","""Build rarefied otu tables containing 100 (-m) to 2000 (-x) sequences in steps of 100 (-s) with 5 (-n) repetions per number of sequences, from /home/qiime_user/otu_table.txt (-i). Write the output files to the /home/qiime_user/rare directory (-o, will be created if it doesn't exist). The name of the output files will be of the form /home/qiime_user/rare/rarefaction_<num_seqs>_<reptition_number>.txt""","""%prog -o /home/qiime_user/rare -m 100 -x 2000 -s 100 -n 5 -i /home/qiime_user/otu_table.txt"""))
script_info['script_usage'].append(("""Example 2""","""Build 8 rarefied otu tables each containing exactly 100 sequences per sample (even depth rarefaction).""","""%prog -o /home/qiime_user/rare -m 100 -x 100 -s 100 -n 8 -i /home/qiime_user/otu_table.txt"""))
script_info['output_description']="""The result of parallel_multiple_rarefactions.py consists of a number of files, which depend on the minimum/maximum number of sequences per samples, steps and iterations. The files have the same otu table format as the input otu_table.txt, and are named in the following way: rarefaction_100_0.txt, where "100" corresponds to the sequences per sample and "0" for the iteration."""

script_info['required_options'] = [\
 make_option('-i', '--input_path',
        help='input filepath, (the otu table) [REQUIRED]'),\
 make_option('-o', '--output_path',
        help="write output rarefied otu tables here makes dir if it doesn't exist [REQUIRED]"),\
 make_option('-m', '--min', type=int,help='min seqs/sample [REQUIRED]'),\
 make_option('-x', '--max', type=int,\
                      help='max seqs/sample (inclusive) [REQUIRED]'),\

]
script_info['optional_options'] = [\
 make_option('-n', '--num-reps', dest='num_reps', default=10, type=int,
        help='num iterations at each seqs/sample level [default: %default]'),\
 make_option('--lineages_included', action='store_true', default=True,
    help='Deprecated: lineages are now included by default. Pass' +\
    ' --supress_lineages_included to prevent output OTU tables' +\
    ' from including taxonomic (lineage) information for each OTU. Note:' +\
    ' this will only work if lineage information is in the input OTU' +\
    ' table.'),
 make_option('--suppress_lineages_included', default=True, 
    action="store_false",dest='lineages_included',
    help='Exclude taxonomic (lineage) information for each OTU.'),
 make_option('-N','--single_rarefaction_fp',action='store',\
           type='string',help='full path to scripts/single_rarefaction.py [default: %default]',\
           default=join(get_qiime_scripts_dir(),'single_rarefaction.py')),\
 make_option('-s', '--step', type=int, default=1,\
                      help='levels: min, min+step... for level <= max [default: %default]'),\
 options_lookup['poller_fp'],\
 options_lookup['retain_temp_files'],\
 options_lookup['suppress_submit_jobs'],\
 options_lookup['poll_directly'],\
 options_lookup['cluster_jobs_fp'],\
 options_lookup['suppress_polling'],\
 options_lookup['job_prefix'],\
 options_lookup['python_exe_fp'],\
 options_lookup['seconds_to_sleep'],\
 options_lookup['jobs_to_start']
]

script_info['version'] = __version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)
    
    # create local copies of command-line options
    input_path = opts.input_path
    output_dir = opts.output_path
    min_seqs = opts.min
    max_seqs = opts.max
    step = opts.step
    if not step > 0:
        print "Error: step size must be greater than 0."
        print "If min = max, just leave step size at 1."
        exit(-1)

    num_reps = opts.num_reps
    lineages_included = opts.lineages_included
    
    single_rarefaction_fp = opts.single_rarefaction_fp
    python_exe_fp = opts.python_exe_fp
    path_to_cluster_jobs = opts.cluster_jobs_fp
    poller_fp = opts.poller_fp
    retain_temp_files = opts.retain_temp_files
    suppress_polling = opts.suppress_polling
    seconds_to_sleep = opts.seconds_to_sleep
    poll_directly = opts.poll_directly
    jobs_to_start = opts.jobs_to_start

    created_temp_paths = []
    
    # split the input filepath into directory and filename, base filename and
    # extension
    input_dir, input_fn = split(input_path)
    input_file_basename, input_file_ext = splitext(input_fn)
    
    # set the job_prefix either based on what the user passed in,
    # or a random string beginning with ALDIV (ALphaDIVersity)
    job_prefix = opts.job_prefix or get_random_job_prefix('RARIF')
    
    # A temporary output directory is created in output_dir named
    # job_prefix. Output files are then moved from the temporary 
    # directory to the output directory when they are complete, allowing
    # a poller to detect when runs complete by the presence of their
    # output files.
    working_dir = '%s/%s' % (output_dir,job_prefix)
    try:
        makedirs(working_dir)
        created_temp_paths.append(working_dir)
    except OSError:
        # working_dir already exists
        pass
    
    # build the filepath for the 'jobs script'
    jobs_fp = '%s/%sjobs.txt' % (output_dir, job_prefix)
    created_temp_paths.append(jobs_fp)
    
    # generate the list of commands to be pushed out to nodes
    commands, job_result_filepaths  = \
     get_job_commands(python_exe_fp,single_rarefaction_fp,job_prefix,\
     input_path,output_dir,working_dir,min_seqs,max_seqs,step,num_reps,
     lineages_included,command_prefix=' ',command_suffix=' ')
     
    # Merge commands into jobs_to_start number of jobs
    commands = merge_to_n_commands(commands,jobs_to_start)
    
    # Set up poller apparatus if the user does not suppress polling
    if not suppress_polling:
        # Write the list of files which must exist for the jobs to be 
        # considered complete
        expected_files_filepath = '%s/expected_out_files.txt' % working_dir
        write_filepaths_to_file(job_result_filepaths,expected_files_filepath)
        created_temp_paths.append(expected_files_filepath)
        
        # Write the mapping file even though no merging is necessary 
        # (get_poller_command requires this, but a future version won't)
        merge_map_filepath = '%s/merge_map.txt' % working_dir
        open(merge_map_filepath,'w').close()
        created_temp_paths.append(merge_map_filepath)
        
        # Create the filepath listing the temporary files to be deleted,
        # but don't write it yet
        deletion_list_filepath = '%s/deletion_list.txt' % working_dir
        created_temp_paths.append(deletion_list_filepath)
        
        if not poll_directly:
            # Generate the command to run the poller, and the list of temp files
            # created by the poller
            poller_command, poller_result_filepaths =\
             get_poller_command(python_exe_fp,poller_fp,expected_files_filepath,\
             merge_map_filepath,deletion_list_filepath,\
             seconds_to_sleep=seconds_to_sleep)
            # append the poller command to the list of job commands
            commands.append(poller_command)
        else:
            poller_command, poller_result_filepaths =\
             get_poller_command(python_exe_fp,poller_fp,expected_files_filepath,\
             merge_map_filepath,deletion_list_filepath,\
             seconds_to_sleep=seconds_to_sleep,\
             command_prefix='',command_suffix='')
        
        created_temp_paths += poller_result_filepaths
        
        if not retain_temp_files:
            # If the user wants temp files deleted, now write the list of 
            # temp files to be deleted
            write_filepaths_to_file(created_temp_paths,deletion_list_filepath)
        else:
            # Otherwise just write an empty file
            write_filepaths_to_file([],deletion_list_filepath)
    
    # write the commands to the 'jobs files'
    write_jobs_file(commands,job_prefix=job_prefix,jobs_fp=jobs_fp)
    
    # submit the jobs file using cluster_jobs, if not suppressed by the
    # user
    if not opts.suppress_submit_jobs:
        submit_jobs(path_to_cluster_jobs,jobs_fp,job_prefix)
        
    if poll_directly:
        try:
            check_call(poller_command.split())
        except CalledProcessError, e:
            print '**Error occuring when calling the poller directly. '+\
            'Jobs may have been submitted, but are not being polled.'
            print str(e)
            exit(-1)    

if __name__ == "__main__":
    main()