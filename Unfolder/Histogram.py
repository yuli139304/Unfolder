
import array
import copy
import numbers
import itertools
import matplotlib.pyplot as plt
#import pandas as pd
import seaborn as sns 
import numpy as np
#import pymc3 as pm
import matplotlib.cm as cm
try:
  import ROOT
except:
  pass
from matplotlib.colors import LogNorm

'''
Class used to represent a 1D histogram with errors.
'''
class H1D:
  '''
  Copy constructor
  '''
  def __init__(self, other):
    try:
      if isinstance(other, ROOT.TH1D):
        self.loadFromROOT(other)
        return
    except:
      pass
    if isinstance(other, H1D):
      self.val   = copy.deepcopy(other.val)
      self.err   = copy.deepcopy(other.err)
      self.x     = copy.deepcopy(other.x)
      self.x_err = copy.deepcopy(other.x_err)
      self.shape = copy.deepcopy(self.val.shape)
    else:
      self.val   = copy.deepcopy(other)
      self.err   = copy.deepcopy(np.sqrt(other))
      self.x     = np.arange(0, float(len(other)))
      self.x_err = 0.5*np.ones(len(self.x))
      self.shape = [len(other)]

  '''
  Fil a histogram bin.
  '''
  def fill(self, x, w):
    i = len(self.val)-1
    for k in range(0, len(self.x)):
      xe = self.x[k] + self.x_err[k]
      if xe > x:
        i = k
        break
    self.val[i] += w
    self.err[i] += w*w
    return i

  '''
  Load a 1D histogram from ROOT.
  '''
  def loadFromROOT(self, rootObj):
    self.val   = np.zeros(rootObj.GetNbinsX(), dtype = np.float64)
    self.err   = np.zeros(rootObj.GetNbinsX(), dtype = np.float64)
    self.x     = np.zeros(rootObj.GetNbinsX(), dtype = np.float64)
    self.x_err = np.zeros(rootObj.GetNbinsX(), dtype = np.float64)
    for i in range(0, rootObj.GetNbinsX()):
      self.val[i]   = rootObj.GetBinContent(i+1)
      self.err[i]   = rootObj.GetBinError(i+1)**2
      self.x[i]     = rootObj.GetXaxis().GetBinCenter(i+1)
      self.x_err[i] = rootObj.GetXaxis().GetBinWidth(i+1)*0.5
      if i == 0:
        self.val[i]+= rootObj.GetBinContent(0)
        self.err[i]+= rootObj.GetBinError(0)**2
      if i == rootObj.GetNbinsX()-1:
        self.val[i]+= rootObj.GetBinContent(rootObj.GetNbinsX()+1)
        self.err[i]+= rootObj.GetBinError(rootObj.GetNbinsX()+1)**2
    self.shape = self.val.shape

  '''
  Export a 1D histogram to ROOT.
  '''
  def toROOT(self, name):
    out = ROOT.TH1D(name, name, len(self.x), array.array('d', np.append(self.x-self.x_err, self.x[-1]+self.x_err[-1])))
    out.SetDirectory(0)
    out.Sumw2()
    for i in range(0, len(self.val)):
      out.SetBinContent(i+1, self.val[i])
      out.SetBinError(i+1, self.err[i]**0.5)
    return out


  '''
  Add histograms.
  '''
  def __add__(self, other):
    h = H1D(self)
    if isinstance(other, numbers.Number):
      for i in range(0, len(other.x)): h.val[i] += other
      for i in range(0, len(other.x)): h.err[i] += other**2
      return h
      
    if len(self.x) != len(other.x): raise 'Trying to add two incompatible histograms'
    for i in range(0, len(other.x)): h.val[i] += other.val[i]
    for i in range(0, len(other.x)): h.err[i] += other.err[i]
    return h

  '''
  Subtract histograms.
  '''
  def __sub__(self, other):
    h = H1D(self)
    if isinstance(other, numbers.Number):
      for i in range(0, len(other.x)): h.val[i] -= other
      for i in range(0, len(other.x)): h.err[i] += other**2
      return h
    if len(self.x) != len(other.x): raise 'Trying to subtract two incompatible histograms'
    for i in range(0, len(other.x)): h.val[i] -= other.val[i]
    for i in range(0, len(other.x)): h.err[i] += other.err[i]
    return h

  '''
  Multiply histogram by scalar
  '''
  def __mul__(self, other):
    if isinstance(other, H1D): raise 'Can only multiply histograms with scalars'
    h = H1D(self)
    for i in range(0, len(self.x)): h.val[i] *= other
    for i in range(0, len(self.x)): h.err[i] *= other**2
    return h

  '''
  Multiply histogram by scalar
  '''
  def __rmul__(self, other):
    if isinstance(other, H1D): raise 'Can only multiply histograms with scalars'
    h = H1D(self)
    for i in range(0, len(self.x)): h.val[i] *= other
    for i in range(0, len(self.x)): h.err[i] *= other**2
    return h

  '''
  Divide histogram bin-by-bin by its bin width.
  '''
  def overBinWidth(self):
    h = H1D(self)
    for i in range(0, len(self.x)):
      f = self.x_err[i]*2.0
      h.err[i] = h.err[i]/f**2
      h.val[i] /= f
    return h

  '''
  Divide histograms.
  '''
  def __truediv__(self, other):
    h = H1D(self)
    if isinstance(other, H1D):
      if len(self.x) != len(other.x): raise 'Trying to divide two incompatible histograms'
      for i in range(0, len(other.x)):
        if other.val[i] == 0: continue
        h.err[i] = h.val[i]**2/(other.val[i]**2)*(h.err[i]/(h.val[i]**2) + other.err[i]/(other.val[i]**2))
        h.val[i] /= other.val[i]
    else:
      for i in range(0, len(other.x)): h.val[i] /= other
      for i in range(0, len(other.x)): h.err[i] /= other**2
    return h

  '''
  Get sum of entries
  '''
  def integral(self):
    s = 0
    se = 0
    for i in range(0, len(self.val)):
      s += self.val[i]
      se += self.err[i]
    return [s, se]

  '''
  Divide histograms with binomial error prop.
  '''
  def divideBinomial(self, other):
    h = H1D(self)
    if isinstance(other, H1D):
      if len(self.x) != len(other.x): raise 'Trying to divide two incompatible histograms'
      for i in range(0, len(other.x)):
        if other.val[i] == 0: continue
        a = h.val[i]
        b = other.val[i]
        da2 = h.err[i]
        db2 = other.err[i]
        eff = a/b
        if eff > 1: eff = 1
        if eff < 0: eff = 0
        h.err[i] = np.abs( ( (1 - 2*eff)*da2 + eff**2 * db2 )/(b**2) )
        h.val[i] = eff
    else:
      for i in range(0, len(other.x)):
        a = h.val[i]
        b = other
        da2 = h.err[i]
        db2 = 0
        eff = a/b
        h.val[i] = eff
        h.err[i] = np.abs( ( (1 - 2*eff)*da2 + eff**2 * db2 )/(b**2) )
    return h

  '''
  Divide a histogram a by a histogram e to get histogram b, propagating the errors under the assumption
  that e is an efficiency histogram defined as a/b.
  FIXME
  '''
  def divideInvertedBinomial(self, other):
    h = H1D(self)
    if isinstance(other, H1D):
      if len(self.x) != len(other.x): raise 'Trying to divide two incompatible histograms'
      for i in range(0, len(other.x)):
        if other.val[i] == 0: continue
        a = h.val[i]
        e = other.val[i]
        da2 = h.err[i]
        de2 = other.err[i]
        b = a/e
        h.err[i] = (b**2*de2 - (1 - 2*e)*da2)/(e**2)
        if h.err[i] < 0: h.err[i] = 0.0
        h.val[i] = b
    return h

  '''
  Divide histograms without propagating errors.
  '''
  def divideWithoutErrors(self, other):
    h = H1D(self)
    if isinstance(other, H1D):
      if len(self.x) != len(other.x): raise 'Trying to divide two incompatible histograms'
      for i in range(0, len(other.x)):
        if other.val[i] == 0: continue
        a = h.val[i]
        b = other.val[i]
        da2 = h.err[i]
        db2 = other.err[i]
        e = a/b
        h.err[i] = da2/b
        h.val[i] = e
    return h


'''
Class used to represent a 2D histogram with errors.
'''
class H2D:
  '''
  Copy constructor
  '''
  def __init__(self, other):
    try:
      if isinstance(other, ROOT.TH2D):
        self.loadFromROOT(other)
        return
    except:
      pass
    if isinstance(other, H2D):
      self.val   = copy.deepcopy(other.val)
      self.err   = copy.deepcopy(other.err)
      self.x     = copy.deepcopy(other.x)
      self.x_err = copy.deepcopy(other.x_err)
      self.y     = copy.deepcopy(other.y)
      self.y_err = copy.deepcopy(other.y_err)
      self.shape = copy.deepcopy(self.val.shape)
    else:
      self.val   = copy.deepcopy(other)
      self.err   = copy.deepcopy(np.sqrt(other))
      self.x     = np.arange(0, float(other.shape[0]))
      self.x_err = 0.5*np.ones(len(self.x))
      self.y     = np.arange(0, float(other.shape[1]))
      self.y_err = 0.5*np.ones(len(self.y))
      self.shape = copy.deepcopy(self.val.shape)

  '''
  Fil a histogram bin.
  '''
  def fill(self, x, y, w = 1):
    i = len(self.x)-1
    j = len(self.y)-1
    for k in range(0, len(self.x)):
      xe = self.x[k] + self.x_err[k]
      if xe > x:
        i = k
        j = len(self.y)-1
        for l in range(0, len(self.y)):
          ye = self.y[l] + self.y_err[l]
          if ye > y:
            i = k
            j = l
            self.val[i, j] += w
            self.err[i, j] += w*w
            return [i, j]
        self.val[i, j] += w
        self.err[i, j] += w*w
        return [i, j]
    # overflow x
    i = len(self.x)-1
    j = len(self.y)-1
    for l in range(0, len(self.y)):
      ye = self.y[l] + self.y_err[l]
      if ye > y:
        j = l
        self.val[i, j] += w
        self.err[i, j] += w*w
        return [i, j]
    self.val[i, j] += w
    self.err[i, j] += w*w
    return [i, j]
    

  '''
  Load a 2D histogram from ROOT.
  '''
  def loadFromROOT(self, rootObj):
    self.val   = np.zeros((rootObj.GetNbinsX(), rootObj.GetNbinsY()), dtype = np.float64)
    self.err   = np.zeros((rootObj.GetNbinsX(), rootObj.GetNbinsY()), dtype = np.float64)
    self.x     = np.zeros(rootObj.GetNbinsX(), dtype = np.float64)
    self.x_err = np.zeros(rootObj.GetNbinsX(), dtype = np.float64)
    self.y     = np.zeros(rootObj.GetNbinsY(), dtype = np.float64)
    self.y_err = np.zeros(rootObj.GetNbinsY(), dtype = np.float64)
    for i in range(0, rootObj.GetNbinsX()):
      for j in range(0, rootObj.GetNbinsY()):
        self.val[i,j]   = rootObj.GetBinContent(i+1, j+1)
        self.err[i,j]   = rootObj.GetBinError(i+1, j+1)**2
    for i in range(0, rootObj.GetNbinsX()):
      self.val[i,0]  += rootObj.GetBinContent(i+1, 0)
      self.err[i,0]  += rootObj.GetBinError(i+1, 0)**2
    for j in range(0, rootObj.GetNbinsY()):
      self.val[0,j]  += rootObj.GetBinContent(0, j+1)
      self.err[0,j]  += rootObj.GetBinError(0, j+1)**2
    for i in range(0, rootObj.GetNbinsX()):
      self.val[i,rootObj.GetNbinsY()-1]  += rootObj.GetBinContent(i+1, rootObj.GetNbinsY()+1)
      self.err[i,rootObj.GetNbinsY()-1]  += rootObj.GetBinError(i+1, rootObj.GetNbinsY()+1)**2
    for j in range(0, rootObj.GetNbinsY()):
      self.val[rootObj.GetNbinsX()-1,j]  += rootObj.GetBinContent(rootObj.GetNbinsX()+1, j+1)
      self.err[rootObj.GetNbinsX()-1,j]  += rootObj.GetBinError(rootObj.GetNbinsX()+1, j+1)**2
    for i in range(0, rootObj.GetNbinsX()):
      self.x[i]       = rootObj.GetXaxis().GetBinCenter(i+1)
      self.x_err[i]   = rootObj.GetXaxis().GetBinWidth(i+1)*0.5
    for j in range(0, rootObj.GetNbinsY()):
      self.y[j]       = rootObj.GetYaxis().GetBinCenter(j+1)
      self.y_err[j]   = rootObj.GetYaxis().GetBinWidth(j+1)*0.5
    self.shape = self.val.shape

  '''
  Export a 2D histogram to ROOT.
  '''
  def toROOT(self, name):
    out = ROOT.TH2D(name, name, len(self.x), array.array('d', np.append(self.x-self.x_err, self.x[-1]+self.x_err[-1])), len(self.y), array.array('d', np.append(self.y-self.y_err, self.y[-1]+self.y_err[-1])))
    out.SetDirectory(0)
    out.Sumw2()
    for i in range(0, len(self.x)):
      for j in range(0, len(self.y)):
        out.SetBinContent(i+1, j+1, self.val[i, j])
        out.SetBinError(i+1, j+1, self.err[i, j]**0.5)
    return out


  '''
  Add histograms.
  '''
  def __add__(self, other):
    h = H2D(self)
    if self.x.shape != other.x.shape: raise 'Trying to add two incompatible histograms'
    for i in range(0, other.x.shape[0]):
      for j in range(0, other.x.shape[1]):
        h.val[i,j] += other.val[i,j]
        h.err[i,j] += other.err[i,j]
    return h

  '''
  Subtract histograms.
  '''
  def __sub__(self, other):
    h = H2D(self)
    if self.x.shape != other.x.shape: raise 'Trying to add two incompatible histograms'
    for i in range(0, other.val.shape[0]):
      for j in range(0, other.val.shape[1]):
        h.val[i,j] -= other.val[i,j]
        h.err[i,j] += other.err[i,j]
    return h

  '''
  Multiply histogram by a scalar.
  '''
  def __mul__(self, other):
    h = H2D(self)
    if isinstance(other, H1D): raise 'Can only multiply histograms with scalars'
    for i in range(0, h.val.shape[0]):
      for j in range(0, h.val.shape[1]):
        h.val[i,j] *= other
        h.err[i,j] *= other**2
    return h

  '''
  Multiply histogram by a scalar.
  '''
  def __rmul__(self, other):
    h = H2D(self)
    if isinstance(other, H1D): raise 'Can only multiply histograms with scalars'
    for i in range(0, h.val.shape[0]):
      for j in range(0, h.val.shape[1]):
        h.val[i,j] *= other
        h.err[i,j] *= other**2
    return h

  '''
  Divide histograms.
  '''
  def __div__(self, other):
    h = H2D(self)
    if self.val.shape != other.val.shape: raise 'Trying to divide two incompatible histograms'
    for i in range(0, other.val.shape[0]):
      for j in range(0, other.val.shape[1]):
        if other.val[i,j] == 0: continue
        h.err[i,j] = h.val[i,j]**2/(other.val[i,j]**2)*(h.err[i,j]/(h.val[i,j]**2) + other.err[i,j]/(other.val[i,j]**2))
        h.val[i,j] /= other.val[i,j]
    return h

  '''
  Transpose all entries.
  '''
  def T(self):
    h = H2D(self)
    tmpx = copy.deepcopy(h.x)
    tmpx_err = copy.deepcopy(h.x_err)
    h.x = copy.deepcopy(h.y)
    h.x_err = copy.deepcopy(h.y_err)
    h.y = copy.deepcopy(tmpx)
    h.y_err = copy.deepcopy(tmpx_err)
    h.val = copy.deepcopy(np.transpose(h.val))
    h.err = copy.deepcopy(np.transpose(h.err))
    h.shape = copy.deepcopy(h.val.shape)
    return h

  '''
  Project into one axis.
  Sums all entries in the axis orthogonal to the one given. 
  '''
  def project(self, axis = 'x'):
    if axis == 'x':
      N = len(self.x)
      h = H1D(np.zeros(N, dtype = np.float64))
      h.x = copy.deepcopy(self.x)
      h.x_err = copy.deepcopy(self.x_err)
    else:
      N = len(self.y)
      h = H1D(np.zeros(N, dtype = np.float64))
      h.x = copy.deepcopy(self.y)
      h.x_err = copy.deepcopy(self.y_err)
    
    if axis == 'x':
      for i in range(0, len(self.x)):
        s = 0
        se = 0
        for j in range(0, len(self.y)):
          s += self.val[i,j]
          se += self.err[i,j]
        h.val[i] = s
        h.err[i] = se
    else:
      for i in range(0, len(self.y)):
        s = 0
        se = 0
        for j in range(0, len(self.x)):
          s += self.val[j,i]
          se += self.err[j,i]
        h.val[i] = s
        h.err[i] = se
    h.shape = h.val.shape
    return h

def plotH2D(h, xlabel = "x", ylabel = "y", title = "Migration matrix M(t, r)", logz = False, fname = "plotH2D.png", vmin = None, vmax = None, fmt = "3.2f"):
  try:
    if h.shape[1] > h.shape[0]:
      fig = plt.figure(figsize=(0.8*h.shape[1], 1.05*h.shape[0]))
    elif h.shape[1] == h.shape[0]:
      fig = plt.figure(figsize=(h.shape[1], 1.05*h.shape[0]))
    else:
      fig = plt.figure(figsize=(h.shape[1], 1.05*0.8*h.shape[0]))
  except:
    fig = plt.figure(figsize=(1, 1.05))

  annot = False
  if fmt != "":
    annot = True
  if isinstance(h, H2D):
    with plt.rc_context(dict(sns.axes_style("whitegrid"),**sns.plotting_context("paper", font_scale=2.5))):
      if logz:
        mat = copy.deepcopy(h)
        for i in range(mat.shape[0]):
          for j in range(mat.shape[1]):
            if mat.val[i, j] < 1e-7:
              mat.val[i, j] = 1e-7
        cax = sns.heatmap(mat.val, cmap="YlGnBu", cbar = True, annot = annot, linewidths=.5, fmt=fmt, square = True, annot_kws={"size": 16}, norm=LogNorm(vmin=vmin, vmax=vmax))
      else:
        cax = sns.heatmap(h.val, cmap="YlGnBu", cbar = True, annot = annot, linewidths=.5, fmt=fmt, square = True, annot_kws={"size": 16}, vmin = vmin, vmax = vmax)
      cax.invert_yaxis()
  else:
    with plt.rc_context(dict(sns.axes_style("whitegrid"),**sns.plotting_context("paper", font_scale=2.5))):
      if logz:
        if vmin == None: vmin = 1e-1
        mat = copy.deepcopy(h)
        for i in xrange(mat.shape[0]):
          for j in xrange(mat.shape[1]):
            if mat[i, j] < vmin:
              mat[i, j] = vmin
        cax = sns.heatmap(mat, cmap="YlGnBu", cbar = True, annot = annot, linewidths=.5, fmt = fmt, square = True, annot_kws={"size": 16}, norm=LogNorm(vmin=vmin, vmax=vmax))
      else:
        cax = sns.heatmap(h, cmap="YlGnBu", cbar = True, annot = annot, linewidths=.5, fmt = fmt, square = True, annot_kws={"size": 16}, vmin = vmin, vmax = vmax)
      cax.invert_yaxis()
  plt.title(title, size = 16)
  plt.ylabel(ylabel)
  plt.xlabel(xlabel)
  #plt.tight_layout()
  plt.savefig(fname)
  plt.close()

def plotH2DWithText(h, x, xlabel = "x", ylabel = "y", title = "Migration matrix M(t, r)", fname = "plotH2D.png"):
  fig = plt.figure(figsize=(h.shape[1], h.shape[0]))
  if isinstance(h, H2D):
    with plt.rc_context(dict(sns.axes_style("whitegrid"),**sns.plotting_context("paper", font_scale=2.5))):
      sns.heatmap(h.val, cmap="YlGnBu", annot = True, linewidths=.5, square = True, annot_kws={"size": 16}, xticklabels = x, yticklabels = x, fmt = "3.2f")
    plt.xticks(rotation = 90)
    plt.yticks(rotation = 0)
  else:
    with plt.rc_context(dict(sns.axes_style("whitegrid"),**sns.plotting_context("paper", font_scale=2.5))):
      sns.heatmap(h, cmap="YlGnBu", annot = True, linewidths=.5, square = True, annot_kws={"size": 16}, xticklabels = x, yticklabels = x, fmt = "3.2f")
    plt.xticks(rotation = 90)
    plt.yticks(rotation = 0)
  plt.title(title, size = 16)
  plt.ylabel(ylabel)
  plt.xlabel(xlabel)
  plt.tight_layout()
  plt.savefig(fname)
  plt.close()

def plotH1D(h, xlabel = "x", ylabel = "Events", title = "", logy = False, fname = "plotH1D.png"):
  fig = plt.figure()
  plt.title(title)
  if isinstance(h, H1D):
    h = {xlabel: h}
  sty = ['ro', 'bv', 'g^', 'm*']
  if logy:
    plt.yscale("log")
  else:
    plt.yscale("linear")
  i = 0
  ymin = 0
  ymax = 0.1
  for n in h:
    k = h[n]
    plt.errorbar(k.x, k.val, k.err**0.5, k.x_err, fmt = sty[i], markersize=10, label = n)
    if np.amax(k.val + k.err**0.5) > ymax: ymax = np.amax(k.val + k.err**0.5)
    if np.amin(k.val - k.err**0.5) < ymin: ymin = np.amin(k.val - k.err**0.5)
    i += 1
  plt.ylabel(ylabel)
  plt.xlabel(xlabel)
  plt.ylim([ymin-0.4*abs(ymin), (1.8 + 0.4*len(h))*ymax])
  plt.legend(loc = "upper right")
  sns.despine()
  plt.tight_layout()
  plt.savefig(fname)
  plt.close()

def plotH1DLines(h, xlabel = "x", ylabel = "Events", title = "", logy = False, fname = "plotH1D.png"):
  fig = plt.figure()
  plt.title(title)
  if isinstance(h, H1D):
    h = {xlabel: h}
  sty = ['ro-', 'bv-', 'g^-', 'm*-']
  i = 0
  ymin = 0
  ymax = 1
  for n in h:
    k = h[n]
    plt.errorbar(k.x, k.val, k.err**0.5, k.x_err, fmt = sty[i], markersize=10, label = n)
    if np.amax(k.val + k.err**0.5) > ymax: ymax = np.amax(k.val + k.err**0.5)
    if np.amin(k.val - k.err**0.5) < ymin: ymin = np.amin(k.val - k.err**0.5)
    i += 1
  plt.ylabel(ylabel)
  plt.xlabel(xlabel)
  plt.ylim([ymin-0.4*abs(ymin), (1.8 + 0.4*len(h))*ymax])
  if logy:
    plt.yscale("log")
  else:
    plt.yscale("linear")
  plt.legend(loc = "upper right")
  sns.despine()
  plt.tight_layout()
  plt.savefig(fname)
  plt.close()

def plotH1DWithText(h, ylabel = "Events", title = "", fname = "plotH1DWithText.png"):
  fig = plt.figure()
  plt.title(title)
  plt.xticks(range(0, len(h.val)), h.x, rotation = 90)
  plt.errorbar(range(0, len(h.val)), h.val, h.err**0.5, [0.5]*len(h.val), fmt = 'r+', markersize=10)
  plt.ylabel(ylabel)
  plt.xlabel("")
  sns.despine()
  plt.tight_layout()
  plt.savefig(fname)
  plt.close()

'''
Return the response matrix by normalising the migration matrix and
then multiplying each truth bin by the efficiency.
Assumes that the truth bins are in rows and reco bins are in columns.
'''
def getNormResponse(migration, efficiency):
  Nt = migration.shape[0]
  Nr = migration.shape[1]
  response = H2D(migration)
  for i in range(0, Nt): # for each truth bin
    rsum = 0.0
    for j in range(0, Nr): # for each reco bin
      rsum += migration.val[i, j]    # calculate the sum of all reco bins in the same truth bin
    # rsum is now the total sum of events that has that particular truth bin
    # now, for each reco bin in truth bin i, divide that row by the total number of events in it
    # and multiply the response matrix by the efficiency
    for j in range(0, Nr):
      response.val[i, j] = migration.val[i, j]/rsum*efficiency.val[i]  # P(r|t) = P(t, r)/P(t) = Mtr*eff(t)/sum_k=1^Nr Mtk
      response.err[i, j] = 0 # FIXME
  return response

