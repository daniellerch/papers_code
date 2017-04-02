#!/usr/bin/python -W ignore
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import shutil
import glob
import random
from multiprocessing import Pool, cpu_count
from scipy import misc


# >> CONFIGURATION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# PATHS USED BY STEGANOGRAPHY TOOLS
# Available at http://dde.binghamton.edu/download/stego_algorithms/
HUGO_BIN="bin/HUGO_like"
WOW_BIN="bin/WOW"
UNIW_BIN="bin/S-UNIWARD"

# PATHS USED BY FEATURE EXTRACTORS
# Available at http://dde.binghamton.edu/download/feature_extractors/
RM_BIN="bin/SRM"

# Number of concurrent processes
NUMBER_OF_PROCESSES=cpu_count()
#NUMBER_OF_PROCESSES=4


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



# {{{ process_extractor()
def process_extractor(fea_ext, f, output_dir, name, remove=False):
   extract_features(fea_ext, f, output_dir, name, remove)
# }}}

# {{{ process_embed_and_extract()
def process_embed_and_extract(fea_ext, f_pgm, 
    name, algo, br, dirB, dirC, output_dir, remove):
   
   hide_and_extract(fea_ext, f_pgm, name, algo, br, dirB, dirC, output_dir, remove)
# }}}

# {{{ hide_and_extract()
# hide info and extract features
def hide_and_extract(fea_ext, f_pgm, name, algo, 
     br, dirB, dirC, output_dir, remove=True):
    fn = extract_name_from_file(f_pgm)

    f_dst=output_dir+"/tmp/"+fn+"_"+str(random.randint(10000000,99999999))+".pgm"
    hide_message(f_pgm, algo, br, output_dir)
    os.rename(f_pgm, f_dst)
    extract_features(fea_ext, f_dst, dirB, name, False)

    hide_message(f_dst, algo, br, output_dir)
    extract_features(fea_ext, f_dst, dirC, name, remove)
# }}}

# {{{ extract_features()
def extract_features(fea_ext, f, odir, name, remove=False):
    if fea_ext=="RM":
        os.makedirs(odir+"/"+name)
        os.system(RM_BIN+" -i "+f+" -O "+odir+"/"+name)

    else:
        print("FATAL ERROR: Unknown feature extractor:", fea_ext)
        return 0

    if remove:
        os.remove(f)
# }}}

# {{{ to_tmp_pgm()
def to_tmp_pgm(f, output_dir):
    fn=extract_name_from_file(f)
    tmp=output_dir+"/tmp/"+fn+"_"+str(random.randint(10000000,99999999))+".pgm"
    I=misc.imread(f);
    misc.imsave(tmp, I);
    return tmp
# }}}

# {{{ read_image_filenames()
def read_image_filenames(base_dir):
    files = glob.glob(base_dir+"/*.pgm")+glob.glob(base_dir+"/*/*.pgm")
    return files
# }}}

# {{{ extract_name_from_file()
def extract_name_from_file(f):
    fn=os.path.basename(f)
    fn=os.path.splitext(fn)[0]
    return fn
# }}}

# {{{ hide_message()
def hide_message(f, algo, br, output):
 
    global HUGO_BIN
    global WOW_BIN
    global UNIW_BIN
    br_str=str(br)

    seed=str( random.randint(-(2**31-1), 2**31-1) )

    if algo=="HUGO":
        if not os.path.exists(HUGO_BIN):
            print("FATAL ERROR: command not found:", HUGO_BIN)
            return -1

        filename=extract_name_from_file(f)
        rdir=output+"/tmp/out_"+str(random.randint(10000000,99999999))
        os.makedirs(rdir)
        os.system(HUGO_BIN+" -r "+seed+" -i "+f+" -O "+rdir+" -a "+br_str)
        os.rename(rdir+"/"+os.path.basename(f), f)
        shutil.rmtree(rdir)

    elif algo=="UNIW":
        if not os.path.exists(UNIW_BIN):
            print("FATAL ERROR: command not found:", UNIW_BIN)
            return -1

        filename=extract_name_from_file(f)
        rdir=output+"/tmp/out_"+str(random.randint(10000000,99999999))
        os.makedirs(rdir)
        os.system(UNIW_BIN+" -r "+seed+" -i "+f+" -O "+rdir+" -a "+br_str)
        os.rename(rdir+"/"+os.path.basename(f), f)
        shutil.rmtree(rdir)

    elif algo=="WOW":         
        if not os.path.exists(WOW_BIN):
            print("FATAL ERROR: command not found:", WOW_BIN)
            return -1

        filename=extract_name_from_file(f)
        rdir=output+"/tmp/out_"+str(random.randint(10000000,99999999))
        os.makedirs(rdir)
        os.system(WOW_BIN+" -r "+seed+" -i "+f+" -O "+rdir+" -a "+br_str)
        os.rename(rdir+"/"+os.path.basename(f), f)
        shutil.rmtree(rdir)

    else:
        print("FATAL ERROR: Unknown algorithm")
        return -1
# }}}

# {{{ prepare_ABC_sets()
def prepare_ABC_sets(input_dir, algo, br, output_dir, fea_ext='RM'):

    if input_dir[-1]=='/':
        input_dir=input_dir[:-1]
    label='ATS_'+fea_ext+'_'+os.path.basename(input_dir)

    if not os.path.isdir(input_dir):                                                             
        print ("FATAL ERROR: input dir does not exists:", input_dir) 
        sys.exit(0) 

    if not os.path.isdir(output_dir+'/'+label):                                             
        os.mkdir(output_dir+'/'+label)

    pool=Pool(processes=NUMBER_OF_PROCESSES) 

    # Al the A sets are the same. We only need one
    dirA=output_dir+'/'+label+'/A_COMMON'
    if os.path.isdir(dirA):
        print("Using data from cache:", dirA)

    else:
        os.mkdir(dirA)
        files = read_image_filenames(input_dir);
        n=1
        for f in files:
            print("A: Extracting", f, "image", n)
            sys.stdout.flush()
            fname=extract_name_from_file(f)

            # The set A is the original testing set. 
            f_pgm=to_tmp_pgm(f, output_dir)
            r=pool.apply_async(
                process_extractor, 
                args=( fea_ext, f_pgm, dirA, fname, True))

            n+=1

    # Prepare sets B and C
    br_str=str(int(float(br)*100)).zfill(3)
    dirB=output_dir+'/'+label+'/B_'+algo+'_'+br_str
    dirC=output_dir+'/'+label+'/C_'+algo+'_'+br_str

    use_BC_cache=False
    if os.path.isdir(dirB) and os.path.isdir(dirC):
        print("Using data from cache:", dirB)
        print("Using data from cache:", dirC)
        use_BC_cache=True
    else:
        if os.path.isdir(dirB):
            shutil.rmtree(dirB)
        if os.path.isdir(dirC):
            shutil.rmtree(dirC)
        os.mkdir(dirB)
        os.mkdir(dirC)

    if not use_BC_cache:
        files = read_image_filenames(input_dir);
        n=1
        for f in files:
            print("BC: Embedding into", f, "image", n)
            sys.stdout.flush()
            fname=extract_name_from_file(f)

            # The set B is the set A with one embedding
            # The set C is the set A with two embedding
            try:
                f_pgm=to_tmp_pgm(f, output_dir)
                r=pool.apply_async(process_embed_and_extract, args=(
                    fea_ext,f_pgm,fname,algo,br,dirB,dirC,output_dir,True))
            
            except Exception, e:
                print("Exception hiding data into:", f, ",",str(e))
                pass

            n+=1

    pool.close()
    pool.join()

# }}}

# {{{ main()
def main():
    if len(sys.argv) < 5:
        print("%s <testing set dir> <output dir> <algo> <bitrate>\n" % sys.argv[0])
        sys.exit(0)

    input_dir=sys.argv[1]
    output_dir=sys.argv[2]
    algo=sys.argv[3]
    bitrate=float(sys.argv[4])

    prepare_ABC_sets(input_dir, algo, bitrate, output_dir)
# }}}


if __name__ == "__main__":
    main()


