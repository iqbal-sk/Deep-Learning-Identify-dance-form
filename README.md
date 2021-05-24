# Deep-Learning-Identify-dance-form
This project is to build a deep learning model that can help classify these images into eight categories of Indian classical dance.

# Note
open "https://nbviewer.jupyter.org/" and paste the notebook link. this is
an independent tool that may work when you are facing any issue with opening notebook in github.
Notebook link for this project - https://github.com/iqbal-sk/Deep-Learning-Identify-dance-form/blob/main/Identify_dance_form.ipynb

# Data Description
- Train dataset - 364 images
- Test dataset - 156 images
- train.csv
- test.csv
- The eight categories of Indian classical dance are as follows:

    Manipuri <br />
    Bharatanatyam <br />
    Odissi <br />
    Kathakali <br />
    Kathak <br />
    Sattriya <br />
    Kuchipudi <br />
    Mohiniyattam <br />

# Running environment
- used Google colab for GPU support so that training of model will take less time.
- uploaded data to drive to provide data for colab environment.

# Model used was vgg_19 with batch normalization
- made last two dense layers of clasifiers as trainable and all remaining layers are pretrained
- changed last dense layer with classes 8 instead of 1000 
- Classifier part of model as below
-   (classifier): Sequential(  <br />
        (0): Linear(in_features=25088, out_features=4096, bias=True) <br />
        (1): ReLU(inplace=True) <br />
        (2): Dropout(p=0.5, inplace=False) <br />
        (3): Linear(in_features=4096, out_features=4096, bias=True) <br />
        (4): ReLU(inplace=True) <br />
        (5): Dropout(p=0.5, inplace=False) <br />
        (6): Linear(in_features=4096, out_features=8, bias=True) <br />
        ) <br />
    
 # Algorithm and functions used in training
 - Evaluation metric used - f1 score
 - Loss function used - crossentropy loss
 - Optimizatino algorithm used - Adam optimization
 - Learning rate - 0.001
 
 
