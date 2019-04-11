#!/usr/bin/env python

#-- Diego Montiel and Kaiyin 2018
#-- Genetics Identificacion Group @ Erasmus MC  --
#-- clean_tree 2.0

import time
import subprocess
import string
import random
import argparse, os
import pandas as pd
from argparse   import ArgumentParser
from subprocess import Popen

def get_arguments():

    parser = ArgumentParser(description="ERASMUS MC \n Clean tree 2.0 for Y chromosome ")    
    parser.add_argument("-bam", "--Bamfile",
        dest="Bamfile", required=False, type=file_exists,
        help="input BAM file", metavar="PATH")    
    
    parser.add_argument("-out", "--output",
            dest="Outputfile", required=True,                        
            help="Folder name containing outputs", metavar="STRING")
    
    parser.add_argument("-hg", "--HG_out",
            dest="HG_out", required=True,                        
            help="Table with HG predictions", metavar="STRING")
    
    parser.add_argument("-int", "--Intermediate",
        dest="Intermediate", required=True, type=file_exists,
        help="Path with intermediate haplogroups branches", metavar="DIR")    
    
    parser.add_argument("-r", "--Reads_thresh",
            help="The minimum number of reads for each base",
            type=int,
            default=50)
    
    parser.add_argument("-q", "--Quality_thresh",
            help="Minimum quality for each read, integer between 10 and 39, inclusive \n [10-40]",
            type=int, required=True)
    
    parser.add_argument("-b", "--Base_majority",
            help="The minimum percentage of a base result for acceptance \n [50-99]",
            type=int, required=True)
            
    args = parser.parse_args()    
    return args

def execute_log(command):
            
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    
    try:
        out, err = proc.communicate(input=input)
        retcode = proc.returncode
        
        return str(out), err, retcode
    except e:
        print("%r %r returned %r" % (command, e))
        raise

def file_exists(file):
    """
    'Type' for argparse - checks that file exists but does not open.
    """
    if not os.path.exists(file):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: file does not exist
        raise argparse.ArgumentTypeError("{0} does not exist".format(file))
    return file
    
        
def execute_mpileup(header, bam_file, pileupfile, Quality_thresh):
    
    if header == "Y":
        tmp_pu = "tmp/tmp.pu"
        
        cmd = "samtools mpileup -AQ{} -r {} {} > {}".format(Quality_thresh, header, bam_file, tmp_pu)
        #print cmd
        subprocess.call(cmd, shell=True)        
        
        cmd = " awk  '{{$1="'"chrY"'"; print}}' {} > {}".format(tmp_pu, pileupfile)
        print("Converting header...")
    
        subprocess.call(cmd, shell=True)
        
        cmd = "rm "+tmp_pu
        subprocess.call(cmd, shell=True)
    else:
        cmd = "samtools mpileup -AQ{} -r {} {} > {}".format(Quality_thresh, header, bam_file, pileupfile)
        #print cmd
        subprocess.call(cmd, shell=True)
    
def chromosome_table(bam_file,bam_folder,file_name, log_output):
    
    output = bam_folder+'/'+file_name+'.chr'
    tmp_output = "tmp_bam.txt"

    f = open(tmp_output, "w")
    subprocess.call(["samtools", "idxstats",bam_file], stdout=f)
    df_chromosome = pd.read_table(tmp_output, header=None)
    total_reads = sum(df_chromosome[2])
    df_chromosome["perc"] = (df_chromosome[2]/total_reads)*100
    df_chromosome = df_chromosome.round(decimals=2)
    df_chromosome['perc'] = df_chromosome['perc'].astype(str) + '%'
    df_chromosome = df_chromosome.drop(columns=[1,3])
    df_chromosome.columns = ['chr','reads','perc']    
    df_chromosome.to_csv(output, index=None, sep="\t")
    
    cmd = "rm "+tmp_output
    subprocess.call(cmd, shell=True)

    if 'Y' in df_chromosome["chr"].values:
        return "Y", total_reads    
    elif 'chrY' in df_chromosome["chr"].values:
        return "chrY", total_reads    
    
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def check_if_folder(path,ext):
    
    list_files = []
    if os.path.isdir(path):
        dirpath = os.walk(path)
        for dirpath, dirnames, filenames in dirpath:
            for filename in [f for f in filenames if f.endswith(ext)]:
                files = os.path.join(dirpath, filename)
                list_files.append(files)
        return list_files
    else:
        return [path]

def get_folder_name(path_file):

    folder      = path_file.split('/')[-1]
    folder_name = os.path.splitext(folder)[0]        
    return folder_name

def create_tmp_dirs(folder):

    flag = True
    if os.path.isdir(folder):    
        while(flag):
            print("WARNING! File "+folder+" already exists, \nWould you like to remove it?")
            choice = input("y/n: ")            
            if str(choice) == "y":
                
                cmd = 'rm -r '+folder
                subprocess.call(cmd, shell=True)
                cmd = 'mkdir '+folder
                subprocess.call(cmd, shell=True)                
                flag = False
                return True
                
            elif str(choice) == "n":                
                flag = False                
                return False
                                  
            else:
                print("Please type y or n")                               
    else:
        cmd = 'mkdir '+folder
        subprocess.call(cmd, shell=True)
        if os.path.exists('tmp'):
            cmd = 'rm -r tmp'
            subprocess.call(cmd, shell=True)
            cmd = 'mkdir tmp'
            subprocess.call(cmd, shell=True)                
        else:
            cmd = 'mkdir tmp'
            subprocess.call(cmd, shell=True)        
        return True
    
def samtools(folder, folder_name, bam_file, Quality_thresh):
    
    #Change this file to Concatenate from the parameter you give    
    args.Markerfile =  'data/positions.txt'
    
    #Reads the file clean_tree.r from the root folder
    rsource = os.path.join(app_folder, 'clean_tree.r')
    
    rscriptn     = '{}/tmp/main.r'.format(app_folder)
    rscriptchr   = '{}/tmp/chrtable.r'.format(app_folder)    
    pileupfile   = '{}/tmp/out.pu'.format(app_folder)
    chr_y_bam    = '{}/tmp/chrY.bam'.format(app_folder)
    
    #Adds the files to the pileup command 
    start_time = time.time()
    
    if not os.path.exists(bam_file+'.bai'): 
        
        bam_file_order = folder+"/"+folder_name+".order.bam"                        
        cmd = "samtools sort -m 2G {} > {}".format(bam_file, bam_file_order)
        #print(cmd)
        print("Sorting Bam file...")
        subprocess.call(cmd, shell=True)
        pileup_cmd = "samtools index {}".format(bam_file_order)
        #print(pileup_cmd)
        print("Indexing Bam file...")
        subprocess.call(pileup_cmd, shell=True)        
        bam_file = bam_file_order
                    
    file_name  = folder_name
    Outputfile = folder+"/"+folder_name+".out"    
    log_output = folder+"/"+folder_name+".log"
    emf_output = folder+"/"+folder_name+".fmf"
    header,total_reads = chromosome_table(bam_file,folder,file_name, log_output)
    execute_mpileup(header, bam_file, pileupfile, Quality_thresh)    
            
      
    print("--- %.2f seconds in run PileUp ---" % (time.time() - start_time))
    
    
    start_time = time.time()    
    roptions1 = """
    Markerfile = '{Markerfile}'       
    Reads_thresh = {Reads_thresh}
    Base_majority = {Base_majority}
    """.format(**vars(args))
    roptions2 = "Pileupfile = '{}'\n\n".format(pileupfile)
    roptions3 = "log_output = '{}'\n".format(log_output)
    roptions4 = "emf_output = '{}'\n".format(emf_output)
    roptions5 = "Outputfile = '{}'\n".format(Outputfile)
    roptions6 = "total_reads = '{}'\n".format(total_reads)    
   
    #Concatenate the files and the script and execute
    rfile = roptions1 + roptions2 + roptions3 + roptions4 + roptions5 + roptions6 + open(rsource).read()
    with open(rscriptn, 'w') as r_out:
        r_out.write(rfile)
    rcmd = 'Rscript --vanilla {}'.format(rscriptn)
    subprocess.call(rcmd, shell=True)        
    
    print("--- %.2f seconds in extracting haplogroups --- " % (time.time() - start_time) )
    print("--- %.2f seconds to run clean_tree  ---" % (time.time() - whole_time))
    return Outputfile

def identify_haplogroup(path_file, intermediate, output):
    
    cmd = "python predict_haplogroup.py -input {} -int {} -out {}".format(path_file, intermediate, output)
    print(cmd)
    subprocess.call(cmd, shell=True)                    
    
if __name__ == "__main__":
            
    whole_time = time.time()
    print("\tErasmus MC Department of Genetic Identification \n\n\tClean tree 2.0 \n")

    args = get_arguments()    
    app_folder = os.path.dirname(os.path.realpath(__file__))    
    sam_file    = ''
    folder_name = ''
    out_path    = args.Outputfile    
    cwd         = os.getcwd()    
    if os.path.isabs(out_path):
        out_folder = out_path
    else:
        if cwd == "/":
            out_folder = out_path
        else:
            out_folder = cwd+"/"+out_path        
    if create_tmp_dirs(out_folder):        
        if args.Bamfile:                
                files = check_if_folder(args.Bamfile,'.bam')
                for path_file in files:            
                    print("Starting...")
                    print(path_file)
                    bam_file = path_file
                    folder_name = get_folder_name(path_file)
                    folder = os.path.join(app_folder,out_folder,folder_name)                            
                    if create_tmp_dirs(folder):                                            
                        output_file = samtools(folder, folder_name, bam_file, args.Quality_thresh)
                identify_haplogroup(out_folder, args.Intermediate, args.HG_out)                                                                        
    else:
        print("--- Clean tree finished... ---")