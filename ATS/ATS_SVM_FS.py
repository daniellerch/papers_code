#!/usr/bin/python -W ignore

from __future__ import print_function
import os
import sys
import glob
import tarfile
from random import randint
import numpy
from sklearn import svm
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn.feature_selection import SelectPercentile, f_classif, chi2, SelectKBest


# {{{ untar_to_tmpdir()
def untar_to_tmpdir(tar_file):

   dirname=os.path.basename(os.path.splitext(tar_file)[0])
   tmpdir1="/tmp/"+str(random.randint(10000000,99999999))
   tmpdir2="/tmp/"+str(random.randint(10000000,99999999))
   tar = tarfile.open(tar_file)
   tar.extractall(tmpdir1)
   tar.close()

   # remove one level
   shutil.move(tmpdir1+'/'+dirname, tmpdir2)
   shutil.rmtree(tmpdir1)

   return tmpdir2
# }}}

# {{{ read_SRM()
def read_SRM(path):

   remove_path=False
   if not os.path.isdir(path):
      path=untar_to_tmpdir(path)
      remove_path=True

   directory = glob.glob(path+"/*")

   submodel_X={}
   submodel_names={}                               
   
   i=0
   for d in directory:
     i+=1
     files = glob.glob(d+"/*.fea")
     for f in files:
       model_name=os.path.splitext(os.path.basename(f))[0]
       features=open(f, 'r').readlines()[0].split(' ');
     
       if model_name not in submodel_X.keys():
         submodel_X[model_name]=[]
         submodel_names[model_name]=[]      
   

       submodel_names[model_name].append(os.path.basename(d))

       fea_line=[]
       features.pop()
       for field in features:
         try:
            fea_line.append(float(field))
         except:
            pass

       if len(submodel_X[model_name]) == 0:
         submodel_X[model_name]=[]
       submodel_X[model_name].append(fea_line)

   for k in submodel_X.keys():
      submodel_X[k]=numpy.array(submodel_X[k])

   if remove_path:
      shutil.rmtree(path)

   return submodel_X, submodel_names
# }}}

# {{{ read_SRM_ABC()
def read_SRM_ABC( pathA, pathB, pathC):

   A, A_names=read_SRM(pathA)
   B, B_names=read_SRM(pathB)
   C, C_names=read_SRM(pathC)

   full_A=[]
   full_B=[]
   full_C=[]
   names=[]
   for k in A.keys():
      if len(full_A)==0:
         full_A=A[k]
         full_B=B[k]
         full_C=C[k]
         names=A_names[k]
         continue

      full_A=numpy.append(full_A, A[k], axis=1)
      full_B=numpy.append(full_B, B[k], axis=1)
      full_C=numpy.append(full_C, C[k], axis=1)

   return full_A, full_B, full_C, names
# }}}

# {{{ grid_search()
def grid_search(X, y):

   # Set the parameters by cross-validation
   tuned_parameters = [{'kernel': ['rbf'], 
                         'gamma': [1e+3,1e-2,1e-1,1e-0,1e-1,1e-2,1e-3,1e-4],
                        'C': [0.25,0.5,1,10,100,10000]}]

   clf = GridSearchCV(svm.SVC(C=1), tuned_parameters)
   clf.fit(X, y)
   
   best_score=0
   best_params={}
   for params, mean_score, scores in clf.grid_scores_:
      if mean_score>best_score:
         best_score=mean_score
         best_params=params

   #print "best_score: %r" % best_score
   #print "best_params: %r" % best_params

   return best_params
# }}}

if len(sys.argv) < 4:
   print("%s <A> <B> <C> <labels>\n" % sys.argv[0])
   sys.exit(0)

directory_A=sys.argv[1]
directory_B=sys.argv[2]
directory_C=sys.argv[3]

A, B, C, names = read_SRM_ABC(directory_A, directory_B, directory_C)

X=numpy.vstack((A, C))
Xt=numpy.hstack(([0]*len(A), [1]*len(C)))

selector = SelectKBest(f_classif, k=500)
selector.fit(X, Xt)
X=selector.transform(X)
B=selector.transform(B)


pm = grid_search(X, Xt)
clf = svm.SVC(kernel=pm['kernel'], C=pm['C'], gamma=pm['gamma'])
clf.fit(X, Xt)

Z = clf.predict(B)

# Calculate accuracy
if len(sys.argv)==5 and os.path.exists(sys.argv[4]):
    with open(sys.argv[4], 'r') as f:
        lines = f.read().splitlines()
    d={}
    for l in lines:
        pair=l.split(":")
        d[pair[0]]=pair[1]

    ok=0
    for i in range(len(Z)):
        if int(d[names[i]]) == Z[i]: ok+=1

    print("Accuracy: ", float(ok)/len(Z))


# Make a prediction
else:
    for i in range(len(Z)):
        r='cover'
        if Z[i]==1: r='stego'
        print(names[i], r)




