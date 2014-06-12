#!/usr/bin/python


'''
Pixel Identification Routines for fil-finder package

The pixels considered are those on the skeletons only. For use only with a skeletonized image.

Contains:
		makefilamentsappear
		isolatefila
		find_filpix
		find_extran

		pix_identify


Requires:
		numpy
		skimage
		ndimage

'''






import numpy as np
import scipy.ndimage as nd
from length import *
import matplotlib.pyplot as p
import skimage.filter as skfilter
import copy


def isolatefilaments(skel_img, size_threshold, pad_size=5):
  '''
  This function separates each filament, over a threshold of number of
  pixels, into its own array with the same dimensions as the inputed image.

  Parameters
  ----------
  skel_img : numpy.ndarray
             the resultant skeletons from the Medial Axis Transform

  mask : numpy.ndarray
         the binary mask from adaptive thresholding

  size_threshold : int
                   sets the pixel size on the size of objects

  Returns
  -------
  skelton_arrays : list
              contains the individual arrays for each skeleton
  mask : numpy.ndarray
         Updated version of the mask where small objects have been eliminated
  num : int
        Number of filaments
  corners : list
            Contains the indices where each skeleton array was taken from
            the original

  '''

  skeleton_arrays = []
  pix_val = []
  corners = []

  # Label skeletons
  labels,num = nd.label(skel_img, eight_con())

  # Remove skeletons which have less pixels than the threshold.
  sums = nd.sum(skel_img, labels, range(1, num + 1))

  for n in range(num):
    if sums[n] < size_threshold:
      skel_img[np.where(labels == n + 1)] = 0

  # Relabel after deleting short skeletons.
  labels,num = nd.label(skel_img, eight_con())
  # Split each skeleton into its own array.
  for n in range(1, num + 1):
    x,y = np.where(labels == n)
    # Make an array shaped to the skeletons size and padded on each edge
    shapes = (x.max() - x.min() + 2 * pad_size, y.max() - y.min() + 2 * pad_size)
    eachfil = np.zeros(shapes)
    for i in range(len(x)):
      eachfil[x[i] - x.min() + pad_size, y[i] - y.min() + pad_size] = 1
    skeleton_arrays.append(eachfil)
    # Keep the coordinates from the original image
    lower = (x.min() - pad_size, y.min() - pad_size)
    upper = (x.max() + pad_size + 1, y.max() + pad_size + 1)
    corners.append([lower, upper])

  return skeleton_arrays, num, corners



def find_filpix(branches,labelfil,final=True):
  '''
   This function identifies the types of pixels contained in the skeleton.
   This is done by creating lists of the pixel values surrounding the pixel
   to be determined.
   For example, consider a 3x3 array about a pixel is
            [1,0,1] \n
 				    [0,1,0] \n
				    [0,1,0] \n
  By considering the surrounding pixels around the center, we get the list,
            [0,0,1,0,1,0,0,1]
  The list is then shifted once to the right giving
            [1,0,0,1,0,1,0,0].
  The shifted list is subtracted from the original yielding
            [-1,0,1,-1,1,-1,0,1].
  The number of 1s (or -1s) give the amount of step-ups around the pixel.
  By comparing the step-ups and the number of non-zero elements in the original
  list, the pixel can be identified into an end point, body point, or an
  intersection point. In this example, the middle pixel is an intersection
  point.

  Parameters
  ----------

  branches : list
             Contains the number of branches in each skeleton.

  labelfil : list
             Contains the arrays of each skeleton.

  final : bool
          If true, corner points, intersections, and body points are all
          labeled as a body point for use when the skeletons have already
          been cleaned.

  Returns
  -------

  fila_pts : list
             All points on the body of each skeleton.

  inters : list
           All points associated with an intersection in each skeleton.

  labelfil : list
             Contains the arrays of each skeleton where all intersections
             have been removed.

  endpts_return : list
                  The end points of each branch of each skeleton.
'''

  initslices = [];initlist = []; shiftlist = [];sublist = [];endpts = [];blockpts = []
  bodypts = [];slices = []; vallist = [];shiftvallist=[];cornerpts = [];delete = []
  subvallist = []
  subslist = [];pix = [];filpix = [];intertemps = [];fila_pts = [];blocks = [];corners = []
  filpts = [];group = [];endpts_return = [];nodes = [];inters = [];repeat = []
  temp_group = [];replace = [];all_pts = [];pairs = []


  for k in range(1,branches+1):
    x,y = np.where(labelfil==k)
    # pixel_slices = np.empty((len(x)+1,8))
    for i in range(len(x)):
      if x[i]<labelfil.shape[0]-1 and y[i]<labelfil.shape[1]-1:
        pix.append((x[i],y[i]))
        initslices.append(np.array([[labelfil[x[i]-1,y[i]+1],labelfil[x[i],y[i]+1],labelfil[x[i]+1,y[i]+1]], \
                                    [labelfil[x[i]-1,y[i]],0,labelfil[x[i]+1,y[i]]], \
                                    [labelfil[x[i]-1,y[i]-1],labelfil[x[i],y[i]-1],labelfil[x[i]+1,y[i]-1]]]))


    filpix.append(pix)
    slices.append(initslices)
    initslices = [];pix= []


  for i in range(len(slices)):
    for k in range(len(slices[i])):
      initlist.append([slices[i][k][0,0],slices[i][k][0,1],slices[i][k][0,2],slices[i][k][1,2],slices[i][k][2,2],slices[i][k][2,1],slices[i][k][2,0],slices[i][k][1,0]])
    vallist.append(initlist)
    initlist = []

  for i in range(len(slices)):
    for k in range(len(slices[i])):
      shiftlist.append(shifter(vallist[i][k],1))
    shiftvallist.append(shiftlist)
    shiftlist = []

  for k in range(len(slices)):
    for i in range(len(vallist[k])):
      for j in range(8):
        sublist.append(int(vallist[k][i][j])-int(shiftvallist[k][i][j]))
      subslist.append(sublist)
      sublist = []
    subvallist.append(subslist)
    subslist = []

  # x represents the subtracted list (step-ups) and y is the values of the surrounding pixels. The categories of pixels are ENDPTS (x<=1), BODYPTS (x=2,y=2),CORNERPTS (x=2,y=3),BLOCKPTS (x=3,y>=4), and INTERPTS (x>=3).
  # A cornerpt is [*,0,0] (*s) associated with an intersection, but their exclusion from
  #		[1,*,0] the intersection keeps eight-connectivity, they are included
  #		[0,1,0] intersections for this reason.
  # A blockpt is  [1,0,1] They are typically found in a group of four, where all four
  #		[0,*,*] constitute a single intersection.
  #		[1,*,*]
  # The "final" designation is used when finding the final branch lengths. At this point, blockpts and cornerpts should be eliminated.
  for k in range(branches):
    for l in range(len(filpix[k])):
      x = [j for j,y in enumerate(subvallist[k][l]) if y==k+1]
      y = [j for j,z in enumerate(vallist[k][l]) if z==k+1]

      if len(x)<=1:
          endpts.append(filpix[k][l])
          endpts_return.append(filpix[k][l])
      elif len(x)==2:
        if final:
          bodypts.append(filpix[k][l])
        else:
          if len(y)==2:
            bodypts.append(filpix[k][l])
          elif len(y)==3:
            cornerpts.append(filpix[k][l])
          elif len(y)>=4:
            blockpts.append(filpix[k][l])
      elif len(x)>=3:
        intertemps.append(filpix[k][l])
    endpts = list(set(endpts))
    bodypts = list(set(bodypts))
    dups = set(endpts) & set(bodypts)
    if len(dups)>0:
          for i in dups:
            bodypts.remove(i)
    #Cornerpts without a partner diagonally attached can be included as a bodypt.
    if len(cornerpts)>0:
        deleted_cornerpts = []
        for i,j in zip(cornerpts,cornerpts):
          if i !=j:
            if distance(i[0],j[0],i[1],j[1])==np.sqrt(2.0):
              proximity = [(i[0],i[1]-1),(i[0],i[1]+1),(i[0]-1,i[1]),(i[0]+1,i[1]),(i[0]-1,i[1]+1),(i[0]+1,i[1]+1),(i[0]-1,i[1]-1),(i[0]+1,i[1]-1)]
              match = set(intertemps) & set(proximity)
              if len(match)==1:
                pairs.append([i,j])
                deleted_cornerpts.append(i)
                deleted_cornerpts.append(j)
        cornerpts = list(set(cornerpts).difference(set(deleted_cornerpts)))

    if len(cornerpts)>0:
      for l in cornerpts:
        proximity = [(l[0],l[1]-1),(l[0],l[1]+1),(l[0]-1,l[1]),(l[0]+1,l[1]),(l[0]-1,l[1]+1),(l[0]+1,l[1]+1),(l[0]-1,l[1]-1),(l[0]+1,l[1]-1)]
        match = set(intertemps) & set(proximity)
        if len(match)==1:
          intertemps.append(l)
          fila_pts.append(endpts+bodypts)
        else:
          fila_pts.append(endpts+bodypts+[l])
          cornerpts.remove(l)
    else:
      fila_pts.append(endpts+bodypts)

    # Reset lists
    cornerpts = []
    endpts = []
    bodypts = []

    if len(pairs)>0:
        for i in range(len(pairs)):
          for j in pairs[i]:
            all_pts.append(j)
    if len(blockpts)>0:
        for i in blockpts:
          all_pts.append(i)
    if len(intertemps)>0:
        for i in intertemps:
          all_pts.append(i)
    # Pairs of cornerpts, blockpts, and interpts are combined into an array. If there is eight connectivity between them, they are labelled as a single intersection.
    arr = np.zeros((labelfil.shape))
    for z in all_pts:
      labelfil[z[0],z[1]]=0
      arr[z[0],z[1]]=1
    lab,nums = nd.label(arr,eight_con())
    for k in range(1,nums+1):
      objs_pix = np.where(lab==k)
      for l in range(len(objs_pix[0])):
        temp_group.append((objs_pix[0][l],objs_pix[1][l]))
      inters.append(temp_group);temp_group = []
  for i in range(len(inters)-1):
    if inters[i]==inters[i+1]:
      repeat.append(inters[i])
  for i in repeat:
    inters.remove(i)

  return fila_pts,inters,labelfil,endpts_return

def find_extran(branches,labelfil):
  '''
  This function's purpose is to identify pixels that are not necessary
  to keep the connectivity of the skeleton. It uses a same process as find_filpix.
  Extraneous pixels tend to be those from former intersections, whose attached
  branch was eliminated in the cleaning process.

  Parameters
  ----------

  branches : list
             Contains the number of branches in each skeleton.

  labelfil : list
             Contains arrays of the labeled versions of each skeleton.

  Returns
  -------

  labelfil : list
             Contains the updated labeled arrays with extraneous pieces
             removed.
  '''
  initslices = [];initlist = []; shiftlist = [];sublist = [];extran= []
  slices = []; vallist = [];shiftvallist=[]
  subvallist = []
  subslist = [];pix = [];filpix = [];filpts = []

  for k in range(1,branches+1):
    x,y = np.where(labelfil==k)
    for i in range(len(x)):
      if x[i]<labelfil.shape[0]-1 and y[i]<labelfil.shape[1]-1:
	  pix.append((x[i],y[i]))
          initslices.append(np.array([[labelfil[x[i]-1,y[i]+1],labelfil[x[i],y[i]+1],labelfil[x[i]+1,y[i]+1]],[labelfil[x[i]-1,y[i]],0,labelfil[x[i]+1,y[i]]],\
            [labelfil[x[i]-1,y[i]-1],labelfil[x[i],y[i]-1],labelfil[x[i]+1,y[i]-1]]]))

    filpix.append(pix)
    slices.append(initslices)
    initslices = [];pix= []

  for i in range(len(slices)):
    for k in range(len(slices[i])):
      initlist.append([slices[i][k][0,0],slices[i][k][0,1],slices[i][k][0,2],slices[i][k][1,2],slices[i][k][2,2],slices[i][k][2,1],slices[i][k][2,0],slices[i][k][1,0]])
    vallist.append(initlist)
    initlist = []

  for i in range(len(slices)):
    for k in range(len(slices[i])):
      shiftlist.append(shifter(vallist[i][k],1))
    shiftvallist.append(shiftlist)
    shiftlist = []

  for k in range(len(slices)):
    for i in range(len(vallist[k])):
      for j in range(8):
        sublist.append(int(vallist[k][i][j])-int(shiftvallist[k][i][j]))
      subslist.append(sublist)
      sublist = []
    subvallist.append(subslist)
    subslist = []

  for k in range(len(slices)):
    for l in range(len(filpix[k])):
      x = [j for j,y in enumerate(subvallist[k][l]) if y==k+1]
      y = [j for j,z in enumerate(vallist[k][l]) if z==k+1]
      if len(x)==0:
        labelfil[filpix[k][l][0],filpix[k][l][1]]=0
      if len(x)==1:
        if len(y)>=2:
          extran.append(filpix[k][l])
          labelfil[filpix[k][l][0],filpix[k][l][1]]=0
    if len(extran)>=2:
      for i in extran:
        for j in extran:
          if i !=j:
            if distance(i[0],j[0],i[1],j[1])==np.sqrt(2.0):
              proximity = [(i[0],i[1]-1),(i[0],i[1]+1),(i[0]-1,i[1]),(i[0]+1,i[1]),(i[0]-1,i[1]+1),(i[0]+1,i[1]+1),(i[0]-1,i[1]-1),(i[0]+1,i[1]-1)]
              match = set(filpix[k]) & set(proximity)
              if len(match)>0:
                for z in match:
                  labelfil[z[0],z[1]]=0
  return labelfil


######################################################################
###				Wrapper Functions
######################################################################


def pix_identify(isolatefilarr,num):
  '''
    This function is essentially a wrapper on find_filpix. It returns the
    outputs of find_filpix in the form that are used during the analysis.

    Parameters
    ----------

    isolatefilarr : list
                    Contains individual arrays of each skeleton.

    num  : int
           The number of skeletons.

    Returns
    -------

    interpts : list
               Contains lists of all intersections points in each skeleton.

    hubs : list
           Contains the number of intersections in each filament. This is
           useful for identifying those with no intersections as their analysis
           is straight-forward.

    ends : list
           Contains the positions of all end points in each skeleton.

    filbranches : list
                  Contains the number of branches in each skeleton.

    labelisofil : list
                  Contains individual arrays for each skeleton where the
                  branches are labeled and the intersections have been removed.
  '''

  interpts = []
  hubs = []
  ends = []
  filbranches=  []
  labelisofil = []

  for n in range(num):
		funcreturn = find_filpix(1, isolatefilarr[n], final=False)
  		interpts.append(funcreturn[1])
  		hubs.append(len(funcreturn[1]))
  		isolatefilarr.pop(n)
  		isolatefilarr.insert(n,funcreturn[2])
  		ends.append(funcreturn[3])

  		label_branch,num_branch = nd.label(isolatefilarr[n],eight_con())
  		filbranches.append(num_branch)
  		labelisofil.append(label_branch)

  return interpts, hubs, ends, filbranches, labelisofil

def extremum_pts(labelisofil,extremum,ends):
  '''
  This function returns the the farthest extents of each filament. This
  is useful for determining how well the shortest path algorithm has worked.

  Parameters
  ----------

  labelisofil : list
                 Contains individual arrays for each skeleton.

  extremum : list
             Contains the extents as determined by the shortest
             path algorithm.

  ends : list
         Contains the positions of each end point in eahch filament.

  Returns
  -------

  extren_pts : list
               Contains the indices of the extremum points.
  '''

  num = len(labelisofil)
  extrem_pts = []

  for n in range(num):
    per_fil = []
    for i,j in ends[n]:
      if labelisofil[n][i,j]==extremum[n][0] or labelisofil[n][i,j]==extremum[n][1]:
        per_fil.append([i,j])
    extrem_pts.append(per_fil)

  return extrem_pts


def make_final_skeletons(labelisofil, inters, verbose=False):
  '''
  Creates the final skeletons outputted by the algorithm.
  '''

  num = len(labelisofil)

  filament_arrays = []

  for n, (skel_array, intersec) in enumerate(zip(labelisofil, inters)):
    copy_array = np.zeros(skel_array.shape, dtype=int)

    for inter in intersec:
      for pts in inter:
        x, y = pts
        copy_array[x,y] = 1

    copy_array[np.where(skel_array >= 1)] = 1

    cleaned_array = find_extran(1, copy_array)

    filament_arrays.append(cleaned_array)

    if verbose:
      p.imshow(cleaned_array)
      p.show()

  return filament_arrays


def recombine_skeletons(skeletons, offsets, orig_size, pad_size, verbose=False):
  '''
  Takes a list of skeleton arrays and combines them back into
  the original array.
  '''

  num  = len(skeletons)

  master_array = np.zeros(orig_size)
  for n in range(num):
    x_off,y_off = offsets[n][0]  # These are the coordinates of the bottom
                                 # left in the master array.
    x_top,y_top = offsets[n][1]

    ## Now check if padding will put the array outside of the original array size
    excess_x_top =  x_top - orig_size[0]

    excess_y_top =  y_top - orig_size[1]

    copy_skeleton = copy.copy(skeletons[n])

    size_change_flag = False

    if excess_x_top > 0:
      copy_skeleton = copy_skeleton[:-excess_x_top,:]
      size_change_flag = True

    if excess_y_top > 0:
      copy_skeleton = copy_skeleton[:,:-excess_y_top]
      size_change_flag = True

    if x_off<0:
      copy_skeleton = copy_skeleton[-x_off:,:]
      x_off = 0
      size_change_flag = True

    if y_off<0:
      copy_skeleton = copy_skeleton[:,-y_off:]
      y_off = 0
      size_change_flag = True

    if verbose & size_change_flag:
      print "REDUCED FILAMENT %s/%s TO FIT IN ORIGINAL ARRAY" %(n, num)

    x,y = np.where(copy_skeleton>=1)
    for i in range(len(x)):
      master_array[x[i]+ x_off,y[i]+ y_off] = 1

  return master_array
