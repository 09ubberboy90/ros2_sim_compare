from matplotlib import pyplot as plt
import os, sys
from os import walk
import re
from collections import defaultdict, OrderedDict
import numpy as np
from numpy.lib.scimath import sqrt
from scipy.interpolate import make_interp_spline, BSpline
from scipy.interpolate import interp1d
from scipy import signal
# import random
from matplotlib import cm
from numpy import linspace
import matplotlib.patches as mpatches
import warnings



SMOOTH_INDEX = 21
POLY_INDEX = 3
if len(sys.argv) < 2:
    folder = ""
else:
    folder = sys.argv[1]
f = []
# exclude = ["data", "data_webots_org", "data_webots_throw", "data_webots", "data_gazebo", "data_gazebo_throw"]
# exclude = [el for el in exclude if el not in folder]
# exclude = ["data", "data_webots"]
for (dirpath, dirnames, filenames) in walk(os.path.join(os.path.dirname(__file__),"../data", folder), topdown=True):
    # dirnames[:] = [d for d in dirnames if d not in exclude]
    f.extend([os.path.join(*dirpath.split("/"), s) for s in filenames])
#tmp = [el for el in f if el[-5:] == "ipynb"]
tmp = [el for el in f if el[-3:] == "csv"]
print(f"Found {len(tmp)}")
types = defaultdict(list)
for el in tmp:
    if "ram" in el:
        types["ram"].append(el)
    else:
        types["cpu"].append(el)

procs = defaultdict(lambda: defaultdict(list))

for key,el in types.items():
    for name in el:    
        existing = []
        with open(name) as f:
            for lines in f.readlines():
                line = lines.split(",")
                p = line[0]
                if p == "ruby":
                    p = "ignition"
                val = line[1:]
                val = [float(x) for x in val]
                counter = 0
                new_p = p
                while new_p in existing:
                    counter += 1
                    new_p = new_p + "_" + str(counter)
                if counter != 0:
                    p = p+"_"+str(counter)
                procs[key][p].append(val)
                existing.append(p)
# colors = {}
# colors.update(mcolors.TABLEAU_COLORS)
# colors.update(mcolors.BASE_COLORS)
# colors.update(mcolors.CSS4_COLORS)
# colors = list(colors.values())
# random.shuffle(colors)

runtime = 0
success =0
fruntime = 0
failure =0
maxtime = 0
fmaxtime = 0
total = 0
with open(os.path.join(os.path.dirname(__file__),"../data", folder, "run.txt")) as f:
    for el in f.readlines():
        splitted = el.split()
        if not "Timeout" == splitted[0]:
            runtime += float(splitted[4])
            total += 1
        if "Completed" == splitted[0]:
            success += 1
            if float(splitted[4]) > maxtime:
                maxtime = float(splitted[4])
        if "Failed" == splitted[0]:
            failure += 1
            if float(splitted[4]) > fmaxtime:
                fmaxtime = float(splitted[4])

    mean = runtime/total
    mean_square = 0
    f.seek(0)
    for el in f.readlines():
        if not "Timeout" == el.split()[0]:
            val = float(el.split()[4])

            mean_square += pow(val-mean, 2)
    stddev = sqrt( mean_square / total)

print(f"\tName & Success & Failure & Timeout & Average Runtime & Standart Deviation\\\\")
print(f"\t{folder} & {success} & {failure} & {150-(success + failure)} & {mean:.2f} & {stddev:.2f} \\\\")
def create_figure(figname, printing=False):

    fig, axs = plt.subplots(2,figsize=(12,8) )

    for axs, (type, proc) in zip(axs, procs.items()):
        cm_subsection = linspace(0.0, 1.0, len(proc.values())+2) # +2 to handle the span
        colors = [ cm.jet(x) for x in cm_subsection ]
        sorted_dict = OrderedDict()

        keys = sorted(proc.keys())
        for key in keys:
            sorted_dict[key] = proc[key]
        #colors.reverse()
        total = None
        length = 0
        for ls in sorted_dict.values():
            tmp = max(map(len, ls))
            if tmp > length:
                length = tmp
        for color, (name, ls) in zip(colors, sorted_dict.items()):
            arr=np.array([xi+[np.nan]*(length-len(xi)) for xi in ls])
            if total is None:
                total = arr
            else:
                arr = np.resize(arr,total.shape[0:2])
                total = np.dstack((arr, total))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                meanarr = np.nanmean(arr, axis=0)
                standard_dev = np.nanstd(arr, axis=0)
            x = np.arange(0, meanarr.shape[0],1)/10 # because recording every 100 ms


            y=signal.savgol_filter(meanarr,
                            SMOOTH_INDEX, # window size used for filtering
                            POLY_INDEX), # order of fitted polynomial
            axs.plot(x, y[0], label=name, color=color)

            lower = meanarr-standard_dev
            high = meanarr+standard_dev
            lower=signal.savgol_filter(lower,
                            SMOOTH_INDEX, # window size used for filtering
                            POLY_INDEX), # order of fitted polynomial
            high=signal.savgol_filter(high,
                            SMOOTH_INDEX, # window size used for filtering
                            POLY_INDEX), # order of fitted polynomial
                        
            for i in range(10):
                if high[0][i] > 300 and type == "cpu":
                    high[0][i] = y[0][i]
            axs.fill_between(x, lower[0], high[0], alpha = 0.5, interpolate=False,color=color)
            axs.set_xlabel("Time (s)")
            if type == "ram":
                axs.set_ylabel("RAM usage (Mb)")
                axs.set_title("RAM usage against time")
            else:
                axs.set_title("CPU usage against time")
                axs.set_ylabel("CPU Usage (% of one core)")
        legend1 = axs.legend( bbox_to_anchor=(1,1.1), loc="upper left")
        axs.axvline(x=mean, ls='--', color=colors[-2], label="Mean success")
        axs.axvspan(mean-stddev, mean+stddev, alpha=0.2, color=colors[-2])

        if failure != 0:
            axs.axvspan(maxtime, x[-1], alpha=0.2, color=colors[-1])
        pmark = mpatches.Patch(facecolor=colors[-1],
                            edgecolor='white',
                            linestyle='--',
                            alpha=0.2,
                            label='Failure Only')
        # axs.annotate(f"{mean:.1f}", 
        #             xy=(mean-max(x)/40, -15), xycoords=("data", "axes points") )

        lines = axs.get_lines()
        legend2 = axs.legend([lines[-1], pmark],['Average Runtime', "Failure Only"], loc="upper right", bbox_to_anchor=(1,1.1))
        axs.add_artist(legend1)
        axs.set_xticks(list(axs.get_xticks())[1:-1] + [mean])
        labels = axs.get_xticklabels()
        for idx, el in enumerate(axs.get_xticks()):
            labels[idx] = f"{el:.2f}"
        labels[-1] = f"\n{mean:.2f}"
        axs.set_xticklabels(labels)

        if printing:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                meanarr = np.nanmean(total, axis=0)
                maxi = np.nanmax(total, axis=0)
                mini = np.nanmin(total, axis=0)
            a = np.nansum(meanarr, axis=1)
            b = np.nansum(maxi, axis=1)
            c = np.nansum(mini, axis=1)
            print(f"\t========={type}=========")
            print(f"\tName & Max & Mean & Min \\\\")
            print(f"\t{folder} & {np.max(b):.0f} & {np.mean(a):.0f} & {np.min(c):.0f} \\\\")
    plt.subplots_adjust(bottom=0.08, top=0.95, hspace=0.26)

    #plt.subplots_adjust(hspace=0.25 + 0.2*(len(lines)-16))
    plt.savefig(os.path.join(os.path.dirname(__file__),f"../data/{folder}/{figname}"), bbox_inches="tight")


create_figure(f"{folder}_smooth.svg", True)
create_figure(f"{folder}_no_smooth.svg",)