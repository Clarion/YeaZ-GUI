#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 15:00:29 2019

This program reads out the images from the nd2 file and creates or
reads the hdf file containing the segmentation.
"""
from nd2reader import ND2Reader
#import matplotlib.pyplot as plt
import numpy as np

import h5py
import os.path
import skimage.io
#import segment as seg
import neural_network as nn



import matplotlib.pyplot as plt
import CellCorrespondance as cc
import matplotlib.pyplot as plt


class Reader:

    def __init__(self, hdfpathname, newhdfname, nd2pathname):


#        Initializes the data corresponding to the sizes of the pictures,
#        the number of different fields of views(Npos) taken in the experiment.
#        And it also sets the number of time frames per field of view.
        self.nd2path = nd2pathname
        self.hdfpath = hdfpathname
        self.newhdfname = newhdfname

        with ND2Reader(self.nd2path) as images:
            self.sizex = images.sizes['x']
            self.sizey = images.sizes['y']
            self.sizec = images.sizes['c']
            self.sizet = images.sizes['t']
            self.Npos  = images.sizes['v']
            self.channel_names = images.metadata['channels']

        #create the labels which index the masks with respect to time and
        #fov indices in the hdf5 file
        self.fovlabels = []
        self.tlabels = []
        self.InitLabels()

        self.default_channel = 0

        self.name = self.hdfpath

        self.predictname = ''
        self.thresholdname = ''
        self.segmentname = ''

#        self.channelwindow = chch.CustomDialog(self)
#
#        if self.channelwindow.exec_():
#
#             self.default_channel = self.channelwindow.button_channel.currentIndex()






#        create an new hfd5 file if no one existing already
        self.Inithdf()




    def InitLabels(self):
        """Create two lists containing all the possible fields of view and time
        labels, in order to access the arrays in the hdf5 file.
        """

        for i in range(0, self.Npos):
            self.fovlabels.append('FOV' + str(i))

        for j in range(0, self.sizet):
            self.tlabels.append('T'+ str(j))



    def Inithdf(self):
        """If the file already exists then it is loaded else
        a new hdf5 file is created and for every fields of view
        a new group is created in the createhdf method
        """

        if not self.hdfpath:
            return self.Createhdf()
        else:
#
            temp = self.hdfpath[:-3]

            self.thresholdname = temp + '_thresholded' + '.h5'
            self.segmentname = temp + '_segmented' + '.h5'
            self.predictname = temp + '_predicted' + '.h5'

#

    def Createhdf(self):

        """In this method, for each field of view one group is created. And
        in each one of these group, there will be for each time frame a
        corresponding dataset equivalent to a 2d array containing the
        corresponding masks data (segmented/thresholded/predicted).
        """
#        print('createhdf')

        self.hdfpath = ''
        templist = self.nd2path.split('/')
        for k in range(0, len(templist)-1):
            self.hdfpath = self.hdfpath+templist[k]+'/'

        self.hdfpath = self.hdfpath + self.newhdfname + '.h5'

        hf = h5py.File(self.hdfpath, 'w')

        for i in range(0, self.Npos):

            grpname = self.fovlabels[i]
            hf.create_group(grpname)

        hf.close()




        for k in range(0, len(templist)-1):
            self.thresholdname = self.thresholdname+templist[k]+'/'
        self.thresholdname = self.thresholdname + self.newhdfname + '_thresholded' + '.h5'

        hf = h5py.File(self.thresholdname,'w')

        for i in range(0, self.Npos):

            grpname = self.fovlabels[i]
            hf.create_group(grpname)

        hf.close()

        for k in range(0, len(templist)-1):
            self.segmentname = self.segmentname+templist[k]+'/'
        self.segmentname = self.segmentname + self.newhdfname + '_segmented' + '.h5'

        hf = h5py.File(self.segmentname,'w')

        for i in range(0, self.Npos):

            grpname = self.fovlabels[i]
            hf.create_group(grpname)

        hf.close()

        for k in range(0, len(templist)-1):
            self.predictname = self.predictname+templist[k]+'/'
        self.predictname = self.predictname + self.newhdfname + '_predicted' + '.h5'

        hf = h5py.File(self.predictname,'w')

        for i in range(0, self.Npos):

            grpname = self.fovlabels[i]
            hf.create_group(grpname)

        hf.close()

    def LoadMask(self, currentT, currentFOV):
        """this method is called when one mask should be loaded from the file
        on the disk to the user's buffer. If there is no mask corresponding
        in the file, it creates the mask corresponding to the given time and
        field of view index and returns an array filled with zeros.
        """

        file = h5py.File(self.hdfpath,'r+')
        if self.TestTimeExist(currentT,currentFOV,file):
            mask = np.array(file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])], dtype = np.uint16)
            file.close()


            return mask


        else:

#            change with Matthias code!

            zeroarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = zeroarray, compression = 'gzip')
            file.close()
            return zeroarray


    def TestTimeExist(self,currentT, currentFOV, file):
        """This method tests if the array which is requested by LoadMask
        already exists or not in the hdf file.
        """

        for t in file['/{}'.format(self.fovlabels[currentFOV])].keys():

            if t == self.tlabels[currentT]:


                return True

        return False



    def SaveMask(self, currentT, currentFOV, mask):
        """This function is called when the user wants to save the mask in the
        hdf5 file on the disk. It overwrites the existing array with the new
        one given in argument.
        If it is a new mask, there should already
        be an existing null array which has been created by the LoadMask method
        when the new array has been loaded/created in the main before calling
        this save method.
        """

        file = h5py.File(self.hdfpath, 'r+')

        if self.TestTimeExist(currentT,currentFOV,file):
            dataset= file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])]
            dataset[:] = mask
            file.close()

        else:

            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = mask, compression = 'gzip')
            file.close()


    def SaveThresholdMask(self, currentT, currentFOV, mask):
        """This function is called when the user wants to save the mask in the
        hdf5 file on the disk. It overwrites the existing array with the new
        one given in argument.
        If it is a new mask, there should already
        be an existing null array which has been created by the LoadMask method
        when the new array has been loaded/created in the main before calling
        this save method.
        """

        file = h5py.File(self.thresholdname, 'r+')

        if self.TestTimeExist(currentT,currentFOV,file):
            dataset = file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])]
            dataset[:] = mask
            file.close()
        else:
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = mask, compression = 'gzip')
            file.close()

    def SaveSegMask(self, currentT, currentFOV, mask):
        """This function is called when the user wants to save the mask in the
        hdf5 file on the disk. It overwrites the existing array with the new
        one given in argument.
        If it is a new mask, there should already
        be an existing null array which has been created by the LoadMask method
        when the new array has been loaded/created in the main before calling
        this save method.
        """

        file = h5py.File(self.segmentname, 'r+')

        if self.TestTimeExist(currentT,currentFOV,file):

            dataset = file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])]
            dataset[:] = mask
            file.close()
        else:
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = mask, compression = 'gzip')
            file.close()



    def TestIndexRange(self,currentT, currentfov):
        """this method receives the time and the fov index and checks
        if it is present in the images data.
        """

        if currentT < (self.sizet-1) and currentfov < self.Npos:
            return True
        if currentT == self.sizet - 1 and currentfov < self.Npos:
            return False
#
    def LoadOneImage(self,currentT, currentfov):
        """This method returns from the nd2 file, the picture requested by the
        main program as an array. It fixes the fov index and iterates over the
        time index.
        """

        with ND2Reader(self.nd2path) as images:
            images.default_coords['v'] = currentfov
            images.default_coords['c'] = self.default_channel
            images.iter_axes = 't'

            if currentT < self.sizet and currentfov < self.Npos:
                im = images[currentT]
                return np.array(im, dtype = np.uint16)
            else:
                return None

    def LoadSeg(self, currentT, currentFOV):


        file = h5py.File(self.segmentname, 'r+')

        if self.TestTimeExist(currentT,currentFOV,file):
            mask = np.array(file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])], dtype = np.uint16)
            file.close()

            return mask


        else:

            zeroarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = zeroarray, compression = 'gzip', compression_opts = 7)

            file.close()
            return zeroarray



    def LoadThreshold(self, currentT, currentFOV):


        file = h5py.File(self.thresholdname, 'r+')

        if self.TestTimeExist(currentT,currentFOV,file):

            mask = np.array(file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])], dtype = np.uint16)
            file.close()

            return mask


        else:

            zeroarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = zeroarray, compression = 'gzip', compression_opts = 7)

            file.close()
            return zeroarray

    def Segment(self, segparamvalue, currentT, currentFOV):
        print(segparamvalue)

#        Check if thresholded version exists
        filethr = h5py.File(self.thresholdname, 'r+')

        if self.TestTimeExist(currentT, currentFOV, filethr):

            tmpthrmask = np.array(filethr['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])])

            segmentedmask = nn.segment(tmpthrmask, segparamvalue)
            filethr.close()

            return segmentedmask


        else:

            filethr.close()
            return np.zeros([self.sizey,self.sizex], dtype = np.uint16)


    def ThresholdPred(self, thvalue, currentT, currentFOV):
        print(thvalue)

        fileprediction = h5py.File(self.predictname,'r+')
        if self.TestTimeExist(currentT, currentFOV, fileprediction):

            pred = np.array(fileprediction['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])])
            fileprediction.close()
            if thvalue == None:
                thresholdedmask = nn.threshold(pred)
            else:
                thresholdedmask = nn.threshold(pred,thvalue)

            return thresholdedmask
        else:
            fileprediction.close()
            return np.zeros([self.sizey, self.sizex], dtype = np.uint16)

#    def LaunchPrediction(self, currentT, currentFOV):


    def TestPredExisting(self, currentT, currentFOV):

        file = h5py.File(self.predictname, 'r+')
        if self.TestTimeExist(currentT, currentFOV, file):
            file.close()
            return True
        else:
            file.close()
            return False





    def LaunchPrediction(self, currentT, currentFOV):

        """It launches the neural neutwork on the current image and creates
        an hdf file with the prediction for the time T and corresponding FOV.
        """

        file = h5py.File(self.predictname, 'r+')

        with ND2Reader(self.nd2path) as images:
            images.default_coords['v'] = currentFOV
            images.default_coords['c'] = self.default_channel
            images.iter_axes = 't'
            temp = images[currentT]
            #temp = np.array(temp, dtype = np.uint16)
            temp = np.array(temp)
            pred = nn.prediction(temp)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = pred, compression = 'gzip', compression_opts = 7)

        file.close()




    def CellCorrespondance(self, currentT, currentFOV):
        print('in cell Correspondance')
        filemasks = h5py.File(self.hdfpath, 'r+')
        fileseg = h5py.File(self.segmentname,'r+')
        if self.TestTimeExist(currentT-1, currentFOV, filemasks):

            if self.TestTimeExist(currentT, currentFOV, fileseg):
                print('inside cellcorerspoindacefunction')
                prevmask = np.array(filemasks['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT-1])])
                nextmask = np.array(fileseg['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])])
                newmask, notifymask = cc.CellCorrespondancePlusTheReturn(nextmask, prevmask)
                filemasks.close()
                fileseg.close()
                return newmask, notifymask

            else:
                filemasks.close()
                fileseg.close()
                null = np.zeros([self.sizey, self.sizex])

                return null, null
        else:

            filemasks.close()
            fileseg.close()
            null = np.zeros([self.sizey, self.sizex])
            return null, null

    def LoadImageChannel(self,currentT, currentFOV, ch):

        with ND2Reader(self.nd2path) as images:
            images.default_coords['v'] = currentFOV
            images.default_coords['t'] = currentT
            images.iter_axes = 'c'
            im = images[ch]
            return np.array(im)