#!/usr/bin/python

from __future__ import print_function

import sys
import multiprocessing

from numpy import *

import scipy
import scipy.spatial.distance as sd

from sklearn import neighbors
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from sklearn import preprocessing

MAX_PROC=8

# {{{ read_features()
def read_features(fea_file):

   fin=open(fea_file, 'r')
   lines = fin.readlines()

   fea=[]
   label=[]

   i=0
   for l in lines:
      features=l.split(',');
      if "stego" in features[len(features)-1]:
         label.append(1)
      else:
         label.append(0)

      fea_line=[]
      features.pop()
      for field in features:
         if len(field)>0:
            fea_line.append(float(field))

      fea.append(fea_line)

   X = array(fea)   
   Xt = array(label)

   return X, Xt
# }}}}

# {{{ Metric()
class Metric(object):
  def __init__(self,dist,name):
    self.dist = dist  # dist(x,y): distance between two points
    self.name = name

  def within(self,A):
    '''pairwise distances between each pair of rows in A'''
    return sd.squareform(sd.pdist(A,self.name),force='tomatrix')

  def between(self,A,B):
    '''cartesian product distances between pairs of rows in A and B'''
    return sd.cdist(A,B,self.name)

  def pairwise(self,A,B):
    '''distances between pairs of rows in A and B'''
    return np.array([self.dist(a,b) for a,b in izip(A,B)])


SquaredL2 = Metric(sd.sqeuclidean,'sqeuclidean')

# }}}


# {{{ adjacency_matrix()
# - W[i,j]=1 when the ith and jth points are neighbors.
# - Otherwise Wij=0.
def adjacency_matrix(X, k):
   # Distances
   metric=SquaredL2
   dist = metric.within(X)

   adj = zeros(dist.shape)  

   # k-nearest neighbors
   nn = argsort(dist)[:,:min(k+1,len(X))]
   
   # nn's first column is the point idx, rest are neighbor idxs
   for idx in nn:
      adj[idx[0],idx[1:]] = 1
      adj[idx[1:],idx[0]] = 1

   n = X.shape[0]
   for i in range(n):
      for j in range(n):
         # geodesic distance inside the manifold
         hk = exp(-(linalg.norm(X[i]-X[j])**2))
         if adj[i,j]==1:
            adj[i,j]*=hk

   return adj
# }}}

# {{{ adjacency_matrix_similarity()
# - W[i,j]=1 when the ith and jth points are neighbors.
# - Otherwise Wij=0.
def adjacency_matrix_similarity(X, Xt, k, ms, md):
   # Distances
   metric=SquaredL2
   dist = metric.within(X)

   adj = zeros(dist.shape)  

   # k-nearest neighbors
   nn = argsort(dist)[:,:min(k+1,len(X))]
   
   # nn's first column is the point idx, rest are neighbor idxs
   for idx in nn:
      adj[idx[0],idx[1:]] = 1
      adj[idx[1:],idx[0]] = 1

   n = X.shape[0]
   for i in range(n):
      for j in range(n):
         # geodesic distance inside the manifold
         hk = exp(-(linalg.norm(X[i]-X[j])**2))
         if Xt[i]==Xt[j]: 
            hk *= ms;
         else:
            hk *= md;

         if adj[i,j]==1:
            adj[i,j]*=hk

   return adj
# }}}

# {{{ laplacian()
# L=D-W
def laplacian(W):

  n_nodes = W.shape[0]
  lap = -asarray(W)  # minus sign leads to a copy
  # set diagonal to zero, in case it isn't already
  lap.flat[::n_nodes + 1] = 0
  d = -lap.sum(axis=0)  # re-negate to get positive degrees

  # put the degrees on the diagonal
  lap.flat[::n_nodes + 1] = d
  return lap
# }}}

# {{{ svm_grid_search()
def svm_grid_search(X, Xt):

   # Set the parameters by cross-validation
   tuned_parameters = [{'kernel': ['rbf'], 
                         'gamma': [1e+3,1e-2,1e-1,1e-0,1e-1,1e-2,1e-3,1e-4],
                        'C': [0.25,0.5,1,10,100,10000]}]

   clf = GridSearchCV(svm.SVC(C=1), tuned_parameters, n_jobs=-1)
   clf.fit(X, Xt)
   return clf.best_params_
# }}}

# {{{ svm_accuracy()
def svm_accuracy(X, Xt, Y, Yt):

   n = X.shape[0]

   pm=svm_grid_search(X, Xt)
   clf=svm.SVC(kernel=pm['kernel'],C=pm['C'],gamma=pm['gamma'],probability=True)
   clf.fit(X, Xt)
   Yt2 = clf.predict(Y)
   
   cnt=0
   for i in range(n):
      if Yt[i]==Yt2[i]:
         cnt=cnt+1

   return 100*float(cnt)/n
# }}}

# {{{ domain_adaptation()
def domain_adaptation(X, Xt, Y, d, k1, k2, eps=1e-8):

   n = X.shape[0]


   pm=svm_grid_search(X, Xt)
   clf=svm.SVC(kernel=pm['kernel'],C=pm['C'],gamma=pm['gamma'],probability=True)
   clf.fit(X, Xt)

   Ty = clf.predict(Y)
   Py = clf.predict_proba(Y)
   Py = array([a for (a, b) in Py])
   Iy = array([i for i in range(n)])
   zipped=zip(Py, Ty, Iy)   
   zipped.sort()
   Py = array([a for (a, b, c) in zipped])
   Ty = array([b for (a, b, c) in zipped])
   Iy = array([c for (a, b, c) in zipped])
      
   Tx = clf.predict(X)
   Px = clf.predict_proba(X)
   Px = array([a for (a, b) in Px])
   Ix = array([i for i in range(n)])
   zipped=zip(Px, Tx, Ix)   
   zipped.sort()
   Px = array([a for (a, b, c) in zipped])
   Tx = array([b for (a, b, c) in zipped])
   Ix = array([c for (a, b, c) in zipped])
   
   # Local geometry (min cost)
   Wx = adjacency_matrix_similarity(X, Xt, k1, 1000, 0.0010)
   Wy = adjacency_matrix(Y, k1)
   Wxy = zeros(shape=(n,n)) 
   for i in range(n):
      # We can not use geodesic distance because they are in different manifolds
      Wxy[Ix[i], Iy[i]]=1

   W=asarray(bmat(((Wx, Wxy),(Wxy.T, Wy))))
   Ll = laplacian(W)

   # Linear algebra
   #vals,vecs = scipy.linalg.eig(A, B)
   vals,vecs = scipy.linalg.eig(Ll)
   idx = argsort(vals)
   for i in xrange(len(idx)):
      if vals[idx[i]] >= eps:
         break
   vecs = vecs.real[:,idx[i:]]

   # Normalization
   for i in xrange(vecs.shape[1]):
      vecs[:,i] /= linalg.norm(vecs[:,i])

   # New Coordinates
   n1=X.shape[0]
   n2=Y.shape[0]
   map1 = vecs[ : n1, : d]
   map2 = vecs[n1 : n1+n2, : d]

   return map1,map2

# }}}



if __name__ == '__main__':

   if len(sys.argv)!=3:
      print("Usage: <fea src> <fea dst>")
      sys.exit(0)
    
   d=2 # dimensions
   X, Xt = read_features(sys.argv[1])
   Y, Yt = read_features(sys.argv[2])
   k1=int(round(sqrt(X.shape[0])))
   k2=k1 # number of neighbors
   noDA_acc = svm_accuracy(X, Xt, Y, Yt)
   Xnew, Ynew = domain_adaptation(X, Xt, Y, d, k1, k2)
   DA_acc = svm_accuracy(Xnew, Xt, Ynew, Yt)

   print("no Da:",noDA_acc, " DA:",DA_acc)
 





