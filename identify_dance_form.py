# -*- coding: utf-8 -*-
"""Identify-dance-form.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Z_Ozvp5OX2jsekJcCOMU854FXpHRTDmp
"""

import os
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import skimage
import statistics
import seaborn as sn
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

import torch
import torch.nn as nn
import torchvision
from torchvision import transforms, utils
from skimage import io, transform
from sklearn.metrics import f1_score
import torchvision.transforms.functional as functional
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim
from torchvision import models

!cp '/content/drive/MyDrive/hackerearth/data.zip' /content/

!unzip /content/data.zip

data_df = pd.read_csv('/content/dataset/train.csv')
data_df.head()

for col in data_df.columns:
  na_count = data_df[col].isna().sum()
  print("nan values count in column {} is {}".format(col, na_count))

dances = ['mohiniyattam', 'odissi', 'bharatanatyam', 'kathakali', 'kuchipudi', 'sattriya', 'kathak', 'manipuri' ]

def show_images(dataframe, columns=3, rows=5):
  fig = plt.figure(figsize=(10, 10))
  for i in range(1, (columns*rows + 1)):
    img = io.imread('/content/dataset/train/'+ dataframe.iloc[i, 0])
    fig.add_subplot(rows, columns, i)
    plt.imshow(img)
plt.show()

train_folder = '/content/dataset/train/'

test_folder = '/content/dataset/test/'

dance_to_number = {'mohiniyattam' : 0, 'odissi' : 1, 'bharatanatyam' : 2, 'kathakali' : 3, 'kuchipudi' : 4, 'sattriya' : 5, 'kathak' : 6, 'manipuri' : 7 }

"""**Custom Dataset class**"""

class IndianDanceDataset(Dataset):
  """
   Args:
            df : Dataframe to be read.
            image_folder (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
  """
  def __init__(self, df, image_folder, transform = None):
    self.dance_df = df
    self.directory = image_folder
    self.transform = transform

  def __len__(self):
    return len(self.dance_df)

  def __getitem__(self, idx):
    
    img_path = os.path.join(self.directory, self.dance_df.iloc[idx, 0])
    dance = self.dance_df.iloc[idx, 1]
    dance = dance_to_number[dance]
    img = io.imread(img_path)

    if self.transform:
      img, dance = self.transform((img, dance))

    return (img, dance)

"""**Split data_df into train and validation set**"""

train_df, validate_df = train_test_split(data_df, test_size=0.1)
print(len(train_df))
print(len(validate_df))

# Checking IndianDanceDataset working properly and inspecting values
train_dataset = IndianDanceDataset(df = train_df, image_folder = train_folder)
val_dataset = IndianDanceDataset(df = validate_df, image_folder = train_folder)

image , label = train_dataset[0]

print(image.shape)
print(image.dtype)
print(label)

plt.imshow(image)
plt.title(label)
plt.show()

"""**Transormations**"""

class Rescale(object):
    """Rescale the image in a sample to a given size.

    Args:
        output_size (tuple or int): Desired output size. If tuple, output is
            matched to output_size. If int, smaller of image edges is matched
            to output_size keeping aspect ratio the same.
    """

    def __init__(self, output_size):
        assert isinstance(output_size, tuple)
        self.output_size = output_size

    def __call__(self, sample):
        image, dance = sample

        new_h, new_w = self.output_size

        new_h, new_w = int(new_h), int(new_w)

        img = skimage.transform.resize(image, (new_h, new_w))

        return (img,dance)


class ToTensor(object):
  """ rotate image by 40 degree angle

    Args:
        sample : Tuple of image and it's label
    """
  def __call__(self, sample):
    img , dance = sample
    img = img.transpose((2,0,1))
    img = img.astype('float32')
    img = torch.from_numpy(img)
    dance = torch.tensor(dance)
    return (img,dance)

class Normalize(object):
  """ Normalize data with provided mean and std

    Args:
        mean : a list of means of channels 
        std : a list of standard deviations of channels
  """
  def __init__(self, mean, std):
    self.mean = mean
    self.std = std

  def __call__(self, sample):
    img, dance = sample
    img = functional.normalize(img, self.mean, self.std)
    return (img, dance)

"""**Training with given Dataset**"""

batch_size = 32              
# Normalizing data with mean and standard deviations of Imagenet dataset
dance_train = IndianDanceDataset(df = train_df,
                                 image_folder = train_folder,
                                 transform = transforms.Compose([Rescale((224,224)), 
                                                                 ToTensor(),
                                                                 Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))

trainloader = DataLoader(dance_train, batch_size = batch_size, shuffle = True)

dance_validate = IndianDanceDataset(df = validate_df,
                                image_folder = train_folder,
                                transform = transforms.Compose([Rescale((224,224)), 
                                                                 ToTensor(),
                                                                 Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))

validate_loader = DataLoader(dance_validate, batch_size = batch_size, shuffle = True)

#inspecting data loader
dataiter = iter(trainloader)
data = dataiter.next()
images , labels = data
print(labels)

print(images[0].shape)
print(labels[0].item())

vgg = models.vgg19_bn(pretrained = True)

print(vgg)

# making every parameter to be non trainable
for param in vgg.parameters():
  param.requires_grad = False

# making only last two dense layers are trainable
vgg.classifier[3] = nn.Linear(4096,4096)
vgg.classifier[6] = nn.Linear(4096,8)

print(vgg)

"""*Trying inference*"""

outputs = vgg(images)

outputs

del outputs

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(device)

vgg = vgg.to(device)
loss_fn = nn.CrossEntropyLoss()
opt = optim.Adam(vgg.parameters(), lr=0.001)

def evaluation(dataloader, model):
    total, correct = 0, 0
    # put model in evaluation mode
    model.eval()
    for data in dataloader:
        inputs, labels = data
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, pred = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (pred == labels).sum().item()
        pred1, labels1 = pred.cpu(), labels.cpu()
        pred1, labels1 = pred1.numpy(), labels1.numpy()
        f1 = f1_score(labels1,pred1,average='micro')
    return [100 * f1, 100 * correct /total]

"""**Train on Normal Train Data**"""

def train(model, trainloader, validate_loader, epochs=5, along_augumented=False, augument_loader=None):
  
  aug_dataiter = None


  loss_train = []
  loss_validate = []
  model_for_epoch = []
  max_epochs = epochs

  train_iters = np.ceil(len(dance_train)/batch_size)
  val_iters = np.ceil(len(dance_validate)/batch_size)

  for epoch in range(max_epochs):
      if along_augumented:
        aug_dataiter = iter(augument_loader)

      loss_epoch_arr = []
      validate_epoch_loss_arr = []
      # train on train-data
      model.train()
      for i, data in enumerate(trainloader, 0):

          inputs, labels = data
          inputs, labels = inputs.to(device), labels.to(device)

          opt.zero_grad()

          outputs = model(inputs)
          loss = loss_fn(outputs, labels)
          loss.backward()
          opt.step()

          if along_augumented:
            aug_data = aug_dataiter.next()
            aug_inputs, aug_labels = aug_data
            aug_inputs, aug_labels = aug_inputs.to(device), aug_labels.to(device)

            opt.zero_grad()

            aug_outputs = model(aug_inputs)
            aug_loss = loss_fn(aug_outputs, aug_labels)
            aug_loss.backward()
            opt.step()
            del aug_inputs, aug_labels, aug_outputs
            torch.cuda.empty_cache()
            loss = (loss + aug_loss) / 2

          print('Train-dataset : Iteration: %d/%d, Loss: %0.2f' % (i+1, train_iters, loss.item()))
              
          del inputs, labels, outputs
          torch.cuda.empty_cache()
          loss_epoch_arr.append(loss.item())
          
      loss_train.append(statistics.mean(loss_epoch_arr))
      scores = evaluation(trainloader, model)

      if along_augumented:
        validation_scores = evaluation(augument_loader, model)
        scores[0] = (scores[0] + validation_scores[0]) / 2
        scores[1] = (scores[1] + validation_scores[1]) / 2
      
          
      print('Epoch: %d/%d, Train score: %0.2f , Train Acc: %0.2f ' % (epoch+1, max_epochs,scores[0], scores[1]))

      # calculate loss in validation-dataset
      model.eval()
      for i, data in enumerate(validate_loader, 0):

          inputs, labels = data
          inputs, labels = inputs.to(device), labels.to(device)

          outputs = model(inputs)
          loss = loss_fn(outputs, labels)

          print('Validation-dataset : Iteration: %d/%d, Loss: %0.2f' % (i+1, val_iters, loss.item()))
              
          del inputs, labels, outputs
          torch.cuda.empty_cache()
          validate_epoch_loss_arr.append(loss.item())
          
      loss_validate.append(statistics.mean(validate_epoch_loss_arr))
      
      model_for_epoch.append(copy.deepcopy(model))
      
  plt.plot(loss_train)
  plt.plot(loss_validate)
  plt.show()

  return model_for_epoch

model_for_epoch = train(vgg, trainloader, validate_loader)

"""**Tracking wrong predictions**"""

class Inspect_IndianDanceDataset(Dataset):
  """
   Args:
            df : Dataframe to be read.
            image_folder (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.

            returns a tuple (image, dance, image_filename)
  """
  def __init__(self, df, image_folder, transform = None):
    self.dance_df = df
    self.directory = image_folder
    self.transform = transform

  def __len__(self):
    return len(self.dance_df)

  def __getitem__(self,idx):
    
    img_path = os.path.join(self.directory,self.dance_df.iloc[idx,0])
    dance = self.dance_df.iloc[idx,1]
    dance = dance_to_number[dance]
    img = io.imread(img_path)
    img_name = self.dance_df.iloc[idx,0]

    if self.transform:
      img,dance = self.transform((img,dance))

    return (img, dance, img_name)

# taking entire validation dataset and checking wrong predictions

dance_train_test = Inspect_IndianDanceDataset(df = validate_df,
                                 image_folder = train_folder,
                                 transform = transforms.Compose([Rescale((224,224)),
                                                                 ToTensor(),
                                                                 Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))

inspect_dataloader = DataLoader(dance_train_test, batch_size = 1, shuffle = False)

def inspect_data(dataloader, model):
  actuals = []
  predicts = []
  for data in dataloader :
    inputs , org_dance_no, img_name = data
    inputs = inputs.to(device)
    outputs = model(inputs)
    _, pred = torch.max(outputs.data, 1)

    pred_dance = number_to_dance[pred.item()]
    actual_dance = number_to_dance[org_dance_no.item()]

    actuals.append(actual_dance)
    predicts.append(pred_dance)

    if pred_dance != actual_dance:
      print('Predicted: ',pred_dance,',    Actual: ',actual_dance, ',  image Name: ',img_name[0])
    
  return actuals, predicts

number_to_dance = {0 :'mohiniyattam', 1 :'odissi', 2 :'bharatanatyam', 3 : 'kathakali' ,
                   4 : 'kuchipudi', 5 : 'sattriya', 6 : 'kathak' , 7 : 'manipuri'}

# taking best_epoch for inspecting

model_to_test = model_for_epoch[2]
y_true, y_pred = inspect_data(inspect_dataloader, model_to_test)

print(*dances)
cm = confusion_matrix(y_true, y_pred, labels = dances)

df_cm = pd.DataFrame(cm, dances, dances)
# plt.figure(figsize=(10,7))
sn.set(font_scale=1.4) # for label size
sn.heatmap(df_cm, annot=True, annot_kws={"size": 16}) # font size
plt.show()

"""**Train Along with augumented Data**"""

class Rotate(object):
  """ rotate image by 40 degree angle

    Args:
        sample : Tuple of image and it's label
    """
  def __call__(self, sample):
    img, dance = sample
    img = skimage.transform.rotate(img,angle = 40, mode='wrap')
    
    return (img,dance)


class Flip_and_ToTensor(object):
  """ Flip image horizontally and transform to tensor

    Args:
        sample : Tuple of image and it's label
    """
  def __call__(self, sample):
    img , dance = sample

    img = np.fliplr(img)  #horizontal flip of image
    
    #transform to Tensor
    img = img.transpose((2,0,1))
    img = img.astype('float32')
    img = torch.from_numpy(img)
    dance = torch.tensor(dance)
    return (img,dance)

# Actual Data
batch_size = 32              
dance_train = IndianDanceDataset(df = train_df,
                                 image_folder = train_folder,
                                 transform = transforms.Compose([Rescale((224,224)), 
                                                                 ToTensor(),
                                                                 Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))

trainloader = DataLoader(dance_train, batch_size = batch_size, shuffle = True)

dance_validate = IndianDanceDataset(df = validate_df,
                                image_folder = train_folder,
                                transform = transforms.Compose([Rescale((224,224)), 
                                                                 ToTensor(),
                                                                 Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))

validate_loader = DataLoader(dance_validate, batch_size = batch_size, shuffle = True)

# Augumented Data
augumented_dance_train = IndianDanceDataset(df = train_df,
                                 image_folder = train_folder,
                                 transform = transforms.Compose([Rescale((224,224)), 
                                                                 Flip_and_ToTensor(),
                                                                 Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))

augumented_trainloader = DataLoader(augumented_dance_train, batch_size = batch_size, shuffle = True)

vgg_2 = models.vgg19_bn(pretrained = True)

# making every parameter to be non trainable
for param in vgg_2.parameters():
  param.requires_grad = False

# making only last two layers as trainable
vgg_2.classifier[3] = nn.Linear(4096,4096)
vgg_2.classifier[6] = nn.Linear(4096,8)

vgg_2 = vgg_2.to(device)
loss_fn = nn.CrossEntropyLoss() 
opt = optim.Adam(vgg_2.parameters(), lr=0.001) # adam optimizer

aug_model_for_epoch = train(vgg_2,trainloader=augumented_trainloader, validate_loader=validate_loader, epochs=3, along_augumented=True, augument_loader=augumented_trainloader)

aug_model_to_test = aug_model_for_epoch[1]

"""**Track wrong predictions in valiation set using model trained on Augumented data**"""

y_true, y_pred = inspect_data(inspect_dataloader, aug_model_to_test)

cm = confusion_matrix(y_true, y_pred, labels = dances)
df_cm = pd.DataFrame(cm, dances, dances)
# plt.figure(figsize=(10,7))
sn.set(font_scale=1.4) # for label size
sn.heatmap(df_cm, annot=True, annot_kws={"size": 16}) # font size
plt.show()

"""# **Conclusion**
Both models trained on actual and augumented d ata having same performance on validation set and both are pretty good

**Testing with test data**
"""

class testDataset(Dataset):
  """
   Args:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
  """
  def __init__(self, csv_path, image_folder, transform = None):
    self.dance_df = pd.read_csv(csv_path)
    self.directory = image_folder
    self.transform = transform

  def __len__(self):
    return len(self.dance_df)

  def __getitem__(self,idx):
    
    img_name = self.dance_df.iloc[idx,0]
    img_path = os.path.join(self.directory,self.dance_df.iloc[idx,0])
    img = io.imread(img_path)

    if self.transform:
      img = self.transform(img)

    return (img,img_name)

class TestRescale(object):
    """Rescale the image in a sample to a given size.

    Args:
        output_size (tuple or int): Desired output size. If tuple, output is
            matched to output_size. If int, smaller of image edges is matched
            to output_size keeping aspect ratio the same.
    """

    def __init__(self, output_size):
        assert isinstance(output_size, tuple)
        self.output_size = output_size

    def __call__(self, image):
        imge = image

        new_h, new_w = self.output_size

        new_h, new_w = int(new_h), int(new_w)

        img = skimage.transform.resize(imge, (new_h, new_w))

        return img


class TestToTensor(object):
  def __call__(self,image):
    img  = image
    img = img.transpose((2,0,1))
    img = img.astype('float32')
    img = torch.from_numpy(img)
    
    return img

class TestNormalize(object):

  def __init__(self, mean, std):
    self.mean = mean
    self.std = std

  def __call__(self,image):
    return functional.normalize(image, self.mean, self.std)

test_dataset = testDataset('/content/dataset/test.csv', test_folder,
                        transform = transforms.Compose([TestRescale((224,224)),
                                                        TestToTensor(),
                                                        TestNormalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))

testloader = DataLoader(test_dataset, batch_size = 1, shuffle = False)

for i, data in enumerate(testloader):
  print(data[0].shape)
  if i == 2:
    break

def test(testloader,model):
  names = []
  ans = []
  for data in testloader :
    inputs , name = data
    inputs = inputs.to(device)
    outputs = model(inputs)
    _, pred = torch.max(outputs.data, 1)

    names.append(name[0])
    dance = number_to_dance[pred.item()]

    print(name[0] , dance)
    ans.append(dance)
  
  data = {'Image': names , 'target': ans}
  df = pd.DataFrame(data)

  return df

# taking epoch 1 model because it has lower gap between train and validate loss
model_to_test = aug_model_for_epoch[1]
test_predictions = test(testloader, model_to_test)

from IPython.display import HTML
import pandas as pd
import numpy as np
import base64

# function that takes in a dataframe and creates a text link to  
# download it (will only work for files < 2MB or so)
def create_download_link(df, title = "Download CSV file", filename = "test-predictions.csv"):  
    csv = df.to_csv(index = False)
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    html = html.format(payload=payload,title=title,filename=filename)
    return HTML(html)

create_download_link(test_predictions)