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

# Number of concurrent processes
NUMBER_OF_PROCESSES=cpu_count()
#NUMBER_OF_PROCESSES=4


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# {{{ process_embedding()
def process_embedding(f_pgm, algo, br, f_dst, output_dir):
    hide_message(f_pgm, algo, br, output_dir)
    os.rename(f_pgm, f_dst)

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
    files = glob.glob(base_dir+"/*.pgm") # +glob.glob(base_dir+"/*.tif")
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

# {{{ gen_testing_set()
def gen_testing_set(cover_dir, perc_stego, algo, bitrate, output_dir):
 
    global NUMBER_OF_PROCESSES
    pool=Pool(processes=NUMBER_OF_PROCESSES) 

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    if not os.path.isdir(output_dir+'/tmp'):
        os.mkdir(output_dir+'/tmp')

    if not os.path.isdir(cover_dir):
        print("FATAL ERROR: cover dir does not exists:", cover_dir)
        sys.exit(0)
    
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)


    if cover_dir[-1]=='/':
        cover_dir=cover_dir[:-1]
    image_dir=output_dir+'/'+algo+'_'+str(bitrate)+'_'+\
        os.path.basename(cover_dir)+'_'+str(perc_stego)

    if os.path.isdir(image_dir):
        print("FATAL ERROR: image dir already exists:", image_dir)
        sys.exit(0)

    os.mkdir(image_dir)
    out_cover_dir=image_dir+'/cover'
    os.mkdir(out_cover_dir)
    out_stego_dir=image_dir+'/stego'
    os.mkdir(out_stego_dir)

    files = read_image_filenames(cover_dir)
    n=1
    for f in files:
        sys.stdout.flush()
        fname=extract_name_from_file(f)
        f_pgm=to_tmp_pgm(f, output_dir)

        try:
            # Use as stego images the percentage requested and move to output dir
            if n<=len(files)*float(perc_stego)/100:
                f_dst=out_stego_dir+'/'+fname+'.pgm'
                with open(image_dir+"/labels.txt", "a+") as myfile:
                    myfile.write(fname+":1\n")

                r=pool.apply_async(process_embedding, 
                  args=( f_pgm, algo, bitrate, f_dst, output_dir))
            
            # Move cover images to output dir
            else:
                with open(image_dir+"/labels.txt", "a+") as myfile:
                    myfile.write(fname+":0\n")
                os.rename(f_pgm, out_cover_dir+'/'+fname+'.pgm')

        except Exception, e:
            print("Error: "+str(e))
            pass

        n+=1

    pool.close()
    pool.join()

# }}}

# {{{ main()
def main():
    if len(sys.argv) < 6:
        print("%s <cover dir> <stego perc> <output dir> <algo> <bitrate>\n" % sys.argv[0])
        sys.exit(0)

    cover_dir=sys.argv[1]
    perc_stego=sys.argv[2]
    output_dir=sys.argv[3]
    algo=sys.argv[4]
    bitrate=float(sys.argv[5])

    gen_testing_set(cover_dir, perc_stego, algo, bitrate, output_dir)
# }}}


if __name__ == "__main__":
    main()


