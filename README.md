# Zuschnitt

A local graphical cutting optimizer for panels/sheets (2D) and linear stock (1D),
similar in functionality to [opticutter.com](https://www.opticutter.com).

## Features

- **2D cutting** – optimizes placement of rectangular pieces on stock sheets using the MAXRECTS algorithm
- **1D cutting** – optimizes cuts from rods, pipes, or lumber using First-Fit Decreasing
- **Kerf support** – accounts for saw blade thickness
- **Rotation** – optional 90° piece rotation to improve fit
- **Grain direction** – lock orientation for wood grain
- **Units** – mm, cm, or inch
- **Visual layout** – color-coded interactive canvas per sheet with zoom/pan
- **Export** – PDF and SVG cutting plans
- **Projects** – save/load `.zusc` JSON project files

## Requirements

- Python 3.11+
- PySide6
- reportlab

## Installation

```bash
pip install -e .
```

## Usage

```bash
zuschnitt                    # open empty project
zuschnitt --open myplan.zusc # open existing project
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
