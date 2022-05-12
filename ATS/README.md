## ATS Steganalysis

Implementation of the method proposed in the paper [Unsupervised steganalysis based on Artificial Training Sets](https://www.sciencedirect.com/science/article/abs/pii/S0952197616000026).

### Example:

#### The testing set:

First, we need to prepare a testing set. 

```bash
$ ./gen_testing_set.py
./gen_testing_set.py <cover dir> <stego perc> <output dir> <algo> <bitrate> 
```

We need cover images, the algorithm and bitrate that we want to use and the percentage of stego images that we want in the testing set. In this example we use 500 images from the BossBase 1.01.

http://dde.binghamton.edu/download/ImageDB/BOSSbase_1.01.zip

And we use as a steganographic algorithm HUGO with a 0.4 bitrate and s 50% of stego images:

http://dde.binghamton.edu/download/stego_algorithms/

Remember to download and compile the steganographic tools that you need. You can change the path of the tools in the config section inside the scripts.

This is the command to generate the testing set:

```bash
./gen_testing_set.py pgm_cover_images 50 out HUGO 0.4
```


#### A, B anc C sets:

The second step is to generate A, B and C sets and extract features using Rich Models:

http://dde.binghamton.edu/download/feature_extractors/

Again, we need to download and compile the tools.

This is the command to prepare the A, B and C sets:

```bash
./prepare_ABC_sets.py out/HUGO_0.4_boss500_50/ out/ HUGO 0.4
```

#### Classification:

The last step is to classify into cover and stego.

```bash
$ ./ATS_SVM_FS.py
./ATS_SVM_FS.py <A> <B> <C> <labels>
```
If we do not give the labels to the script it performs a prediction. But in our case, as far as we know the labels of the testing set, the script can calculate the accuracy of the prediction:

```bash
$ ./ATS_SVM_FS.py
./ATS_SVM_FS.py out/ATS_RM_HUGO_0.4_boss500_50/A_COMMON/ out/ATS_RM_HUGO_0.4_boss500_50/B_HUGO_040 out/ATS_RM_HUGO_0.4_boss500_50/C_HUGO_040 out/HUGO_0.4_boss500_50/labels.txt
Accuracy:  0.828
```


