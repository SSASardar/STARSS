"""
QUICK REFERENCE:
- Colours:       stylesheet.COLORS['blue']   -> '#1f77b4'
- Colourmaps:    stylesheet.COLORMAPS['heat'] -> 'viridis'
- Palettes:     stylesheet.SCENARIO_PALETTES['default'] -> list of hex colors
- Standard use: ax.plot(x, y, color=plot_style.COLORS['red'])
- Heatmaps:     sns.heatmap(data, cmap=plot_style.COLORMAPS['diverging'])
"""

"""
stylesheet.py - Centralized colors and matplotlib settings for PhD thesis.
Import this at the start of every plotting script.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl

# ============================================================
# 1. CATEGORICAL COLORS (for lines, bars, scatter categories)
#    Change these to change every plot across all papers.
# ============================================================
COLORS = {
    'blue':    '#1f77b4',
    'orange':  '#ff7f0e',
    'green':   '#2ca02c',
    'red':     '#d62728',
    'purple':  '#9467bd',
    'brown':   '#8c564b',
    'pink':    '#e377c2',
    'gray':    '#7f7f7f',
    'olive':   '#bcbd22',
    'cyan':    '#17becf',
    'teal':    '#008080',
    'coral':   '#ff6b6b',
    'gold':    '#ffd700',
    'navy':    '#000080',
    'maroon':  '#800000',
    'strat':'#DEECF8',
    'growth':'#A6C5E8',
    'mature':'#72A4D7',
    'decay':'#3F7CC0',
    'black' : '#000000'
    }

# ============================================================
# 2. CONTINUOUS COLORMAPS (for heatmaps, density, contours)
# ============================================================
COLORMAPS = {
    'heat':       'viridis',     # Best all-purpose
    'heat_warm':  'inferno',     # Warmer, good for intensity
    'heat_cool':  'cividis',     # Colorblind-friendly cool
    'diverging':  'RdBu_r',      # Data with meaningful zero midpoint
    'sequential': 'Blues',       # Clean monochrome
    'density':    'plasma'       # Good for scatter density
}

# ============================================================
# 3. SCENARIO PALETTES (map your specific simulation cases)
#    Add your own here. Access via: COLORS_BY_SCENARIO['your_key']
# ============================================================
SCENARIO_PALETTES = {
    # Default 5-color palette
    'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],

    # Example: Temperature simulation
    'temperature': ['#313695', '#4575b4', '#74add1', '#abd9e9',
                    '#fee090', '#fdae61', '#f46d43', '#d73027'],

    # Example: Error rates (sequential purple)
    'error_rates': ['#f7fcfd', '#e0ecf4', '#bfd3e6', '#9ebcda',
                    '#8c96c6', '#8c6bb1', '#88419d', '#6e016b'],

    # Example: Performance metrics
    'performance': ['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4',
                    '#1d91c0', '#225ea8', '#0c2c84']
}

# ============================================================
# 4. MATPLOTLIB GLOBAL SETTINGS (applied on import)
# ============================================================

# Figure sizing
plt.rcParams['figure.figsize'] = (5.5, 4.0)
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

# Fonts
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['font.size'] = 9
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 8
plt.rcParams['ytick.labelsize'] = 8
plt.rcParams['legend.fontsize'] = 8

# Axes
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['xtick.direction'] = 'out'
plt.rcParams['ytick.direction'] = 'out'
plt.rcParams['xtick.major.width'] = 0.8
plt.rcParams['ytick.major.width'] = 0.8
plt.rcParams['xtick.major.size'] = 4
plt.rcParams['ytick.major.size'] = 4

# Legend
plt.rcParams['legend.frameon'] = True
plt.rcParams['legend.framealpha'] = 0.9
plt.rcParams['legend.edgecolor'] = 'black'
plt.rcParams['legend.fancybox'] = False

# Default color cycle (so plt.plot() auto-cycles through your COLORS)
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=list(COLORS.values()))

# Default colormap (so imshow/heatmap uses this unless you override)
plt.rcParams['image.cmap'] = COLORMAPS['heat']
