"""Plot functions for reservoir model"""

import IPython.display as ipy_disp
import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt
from mpl_tools.misc import (axprops, fig_colorbar, fig_placement_load,
                            freshfig, is_notebook_or_qt)
from pylib.dict_tools import DotDict


def setup():
    if is_notebook_or_qt:
        mpl.rcParams.update({'font.size': 13})
        mpl.rcParams["figure.figsize"] = [9, 7]
    else:
        mpl.use("Qt5Agg")
        plt.ion()
        fig_placement_load()

def center(E):
    return E - E.mean(axis=0)


def display(animation):
    if is_notebook_or_qt:
        ipy_disp.display(ipy_disp.HTML(animation.to_jshtml()))
    else:
        plt.show(block=False)

COORD_TYPE = "relative"
def lims(self):
    if "rel" in COORD_TYPE:
        Lx, Ly = 1, 1
    elif "abs" in COORD_TYPE:
        Lx, Ly = self.Lx, self.Ly
    elif "ind" in COORD_TYPE:
        Lx, Ly = self.Nx, self.Ny
    return Lx, Ly

def field(self, ax, zz, **kwargs):
    """Contour-plot the field contained in `zz`."""

    # Need to transpose coz model assumes shape (Nx, Ny),
    # and contour() uses the same orientation as array printing.
    Z = zz.reshape(self.shape).T

    Lx, Ly = lims(self)

    ax.set(**axprops(kwargs))

    # ax.imshow(Z[::-1])
    collections = ax.contourf(
        Z, **kwargs,
        # Using origin="lower" puts the points in the gridcell centers.
        # This means that the plot wont extend all the way to the edges.
        # Unfortunately, there does not seem to be a way to pad the margins,
        # except manually padding Z on all sides, or using origin=None
        # (the mpl default), which would be wrong because it merely
        # stretches rather than pads.
        origin="lower", extent=(0, Lx, 0, Ly))

    ax.set_xlim((0, Lx))
    ax.set_ylim((0, Ly))

    if ax.is_first_col():
        ax.set_ylabel("y")
    if ax.is_last_row():
        ax.set_xlabel("x")

    return collections


def nRowCol(nTotal, wh_ratio=None):
    "Return `int` nrows and ncols such that `nTotal ≈ nrows*ncols`."

    # Aspect ratio: default from mpl.rc.figsize
    if wh_ratio is None:
        w, h = mpl.rcParams["figure.figsize"]
        wh_ratio = w/h

    nrows = int(np.sqrt(nTotal)//wh_ratio)
    ncols = nTotal//nrows

    if nrows*ncols < nTotal:
        ncols += 1

    return nrows, ncols


def subplots(self,
             fignum, plotter, ZZ,
             figsize=None,
             title="",
             ax_text_color="w",
             colorbar=True,
             **kwargs):

    nrows, ncols = nRowCol(min(12, len(ZZ)))

    fig, axs = freshfig(fignum, figsize=figsize,
                        nrows=nrows, ncols=ncols,
                        sharex=True, sharey=True)

    # Turn off redundant axes
    for ax in axs[len(ZZ):]:
        ax.set_visible(False)

    hh = []
    for i, (ax, Z) in enumerate(zip(axs.ravel(), ZZ)):

        # See if ZZ is list/array or dict
        if isinstance(ZZ, dict):
            label = Z
            Z = ZZ[Z]
        else:
            label = i

        # Label
        ax.text(0, 1, label, ha="left", va="top",
                c=ax_text_color, size=12, transform=ax.transAxes)

        # Call plotter
        hh.append(plotter(self, ax, Z, **kwargs))

    if colorbar:
        fig_colorbar(fig, hh[0])

    if title:
        fig.suptitle(title)

    return fig, axs, hh

def oilfields(self, fignum, water_sat_fields, **kwargs):
    return subplots(self, fignum, oilfield, **kwargs)


# Colormap for saturation
lin_cm = mpl.colors.LinearSegmentedColormap.from_list
def ccnvrt(c): return np.array(mpl.colors.colorConverter.to_rgb(c))


# Plain:
cOil   = "red"
cWater = "blue"
# Pastel/neon:
# cWater = "#01a9b4"
# cOil   = "#d8345f"
# Pastel:
# cWater = "#086972"
# cOil   = "#e58a8a"
# middle = .3*ccnvrt(cWater) + .7*ccnvrt(cOil)
# cm_ow = lin_cm("", [cWater,middle,cOil])
# Pastel:
cm_ow = lin_cm("", [(0, "#1d9e97"), (.3, "#b2e0dc"), (1, "#f48974")])

# cm_ow = mpl.cm.viridis


def oilfield(self, ax, ss, **kwargs):
    levels = np.linspace(0 - 1e-7, 1 + 1e-7, 11)
    return field(self, ax, 1-ss, levels=levels, cmap=cm_ow, **kwargs)


def corr_field(self, ax, A, b, title="", **kwargs):
    N = len(b)
    # CovMat = X.T @ X / (N-1)
    # CovMat = np.cov(E.T)
    # vv = diag(CovMat)
    # CorrMat = CovMat/sqrt(vv)/sqrt(vv[:,None])
    # corrs = CorrMat[i]
    A     = center(A)
    b     = center(b)
    covs  = b @ A / (N-1)
    varA  = np.sum(A*A, 0) / (N-1)
    varb  = np.sum(b*b, 0) / (N-1)
    corrs = covs/np.sqrt(varb)/np.sqrt(varA)

    ax.set(title=title)
    cc = field(self, ax, corrs, levels=np.linspace(-1, 1, 11),
               cmap=mpl.cm.bwr, **kwargs)
    return cc


def corr_field_vs(self, ax, E, xy, title="", **kwargs):
    i = self.xy2ind(*xy)
    b = E[:, i]
    cc = corr_field(self, ax, E, b, title, **kwargs)
    ax.plot(*xy, '*k', ms=4)
    return cc

def scale_well_geometry(self, ww):
    """
    Wells use absolute scaling.
    Scale to coord_type instead.
    """
    ww = ww.copy()  # dont overwrite
    if "rel" in COORD_TYPE:
        s = 1/self.Lx, 1/self.Ly
    elif "abs" in COORD_TYPE:
        s = 1, 1
    elif "ind" in COORD_TYPE:
        s = self.Nx/self.Lx, self.Ny/self.Ly
    ww[:, :2] = ww[:, :2] * s
    return ww


def well_scatter(self, ax, ww, inj=True, text=True, color=None):
    ww = scale_well_geometry(self, ww)

    # Style
    if inj:
        c = "w"
        d = "k"
        m = "v"
    else:
        c = "k"
        d = "w"
        m = "^"

    if color:
        c = color

    # Markers
    # sh = ax.plot(*ww.T[:2], m+c, ms=16, mec="k", clip_on=False)
    sh = ax.scatter(*ww.T[:2], s=16**2, c=c, marker=m, clip_on=False,
                    zorder=1.5  # required on Jupypter
                    )

    # Text labels
    if text:
        if not inj:
            ww.T[1] -= 0.01
        for i, w in enumerate(ww):
            ax.text(*w[:2], i, color=d, ha="center", va="center")

    return sh


def production1(ax, production, obs=None):
    hh = []
    tt = 1+np.arange(len(production))
    for i, p in enumerate(1-production.T):
        hh += ax.plot(tt, p, "-", label=i)

    if obs is not None:
        for i, y in enumerate(1-obs.T):
            ax.plot(tt, y, "*", c=hh[i].get_color())

    ax.legend(title="Prod.\nwell #.", loc="upper left", bbox_to_anchor=(1, 1), ncol=3)
    ax.set_ylabel("Oil saturation (rel. production)")
    ax.set_xlabel("Time index")
    ax.set_ylim(-0.01, 1.01)
    return hh

# TODO: implement with plotting.subplots
def productions(fignum, dct, nProd=None, figsize=None, title=""):
    if nProd is None:
        nProd = dct.Truth.shape[1]
        nProd = min(24, nProd)
    nrows, ncols = nRowCol(nProd)
    fig, axs = freshfig(fignum, figsize=figsize,
                        ncols=ncols, nrows=nrows,
                        sharex=True, sharey=True)
    fig.suptitle("Oil productions " + title)

    # Turn off redundant axes
    for ax in axs.ravel()[nProd-1:]:
        ax.set_visible(False)

    # Line styling
    def style(label):
        style = DotDict(
            label=label,
            c="k", alpha=1.0, lw=0.5,
            ls="-", marker="", ms=4,
        )
        if label == "Truth":
            style.lw     = 2
            style.zorder = 2
        if label == "Noisy":
            style.ls     = ""
            style.marker = "*"
        if label == "Prior":
            style.c     = "C0"
            style.alpha = .2
        if label == "ES":
            style.c     = "C1"
            style.alpha = .2
        return style

    # For each well
    for i in range(nProd-1):
        ax = axs.ravel()[i]
        ax.text(1, 1, f"Well {i}" if i == 0 else i, c="k", size=12,
                ha="right", va="top", transform=ax.transAxes)

        for label, series in dct.items():
            ll = ax.plot(1 - series.T[i], **style(label))
            plt.setp(ll[1:], label="_nolegend_")

        # Legend
        if i == nProd-2:
            leg = ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
            for ln in leg.get_lines():
                ln.set(alpha=1, linewidth=max(1, ln.get_linewidth()))


def oilfield_means(self, fignum, water_sat_fields, title="", **kwargs):
    ncols = 2
    nAx   = len(water_sat_fields)
    nrows = int(np.ceil(nAx/ncols))
    fig, axs = freshfig(fignum, figsize=(8, 4*nrows),
                        ncols=ncols, nrows=nrows, sharex=True, sharey=True)

    fig.subplots_adjust(hspace=.3)
    fig.suptitle(f"Oil saturation (mean fields) - {title}")
    for i, (ax, label) in enumerate(zip(axs.ravel(), water_sat_fields)):

        field = water_sat_fields[label]
        if field.ndim == 2:
            field = field.mean(axis=0)

        handle = oilfield(self, ax, field, title=label, **kwargs)

    fig_colorbar(fig, handle)


def correlation_fields(self, fignum, field_ensembles, xy_coord, title="", **kwargs):
    field_ensembles = {k: v for k, v in field_ensembles.items() if v.ndim == 2}

    ncols = 2
    nAx   = len(field_ensembles)
    nrows = int(np.ceil(nAx/ncols))
    fig, axs = freshfig(fignum, figsize=(8, 4*nrows),
                        ncols=ncols, nrows=nrows, sharex=True, sharey=True)

    fig.subplots_adjust(hspace=.3)
    fig.suptitle(title)
    for i, ax in enumerate(axs.ravel()):

        if i >= nAx:
            ax.set_visible(False)
        else:
            label  = list(field_ensembles)[i]
            field  = field_ensembles[label]
            handle = corr_field_vs(self, ax, field, xy_coord, label, **kwargs)

    fig_colorbar(fig, handle, ticks=[-1, -0.4, 0, 0.4, 1])


def dashboard(self, saturation, production, pause=200, animate=True, title="", **kwargs):
    fig, axs = freshfig(231, ncols=2, nrows=2, figsize=(12, 10))
    if is_notebook_or_qt:
        plt.close()  # ttps://stackoverflow.com/q/47138023

    tt = np.arange(len(saturation))

    axs[0, 0].set_title("Oil saturation (Initial)")
    axs[0, 0].cc = oilfield(self, axs[0, 0], saturation[0], **kwargs)
    axs[0, 0].set_ylabel(f"y ({COORD_TYPE})")

    axs[0, 1].set_title("Oil saturation")
    axs[0, 1].cc = oilfield(self, axs[0, 1], saturation[-1], **kwargs)
    well_scatter(self, axs[0, 1], self.injectors)
    well_scatter(self, axs[0, 1], self.producers, False,
                 color=[f"C{i}" for i in range(len(self.producers))])

    axs[1, 0].set_title("Saturation (production)")
    axs[1, 0].set(ylim=(0, 1))
    prod_handles = production1(axs[1, 0], production)
    axs[1, 0].legend(title="Well num.", loc="upper left", bbox_to_anchor=(1, 1), ncol=3)

    axs[1, 1].set_visible(False)

    # fig.tight_layout()
    fig_colorbar(fig, axs[0, 0].cc)

    if title:
        fig.suptitle(title)

    if animate:
        from matplotlib import animation

        def update_fig(iT):
            # Update field
            for c in axs[0, 1].cc.collections:
                try:
                    axs[0, 1].collections.remove(c)
                except ValueError:
                    pass  # occurs when re-running script
            axs[0, 1].cc = oilfield(self, axs[0, 1], saturation[iT], **kwargs)

            # Update production lines
            if iT >= 1:
                for h, p in zip(prod_handles, 1-production.T):
                    h.set_data(tt[:iT-1], p[:iT-1])

        ani = animation.FuncAnimation(
            fig, update_fig, len(tt), blit=False, interval=pause)

        return ani