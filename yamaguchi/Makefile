.PHONY: help env auth ingest normalise lulc match attribute hipi figures all clean

help:
	@echo "Targets:"
	@echo "  env        Create conda environment from env/environment.yml"
	@echo "  auth       Run earthengine and earthaccess auth helpers"
	@echo "  ingest     Pull DW + Landsat ST scenes (Steps 2-3)"
	@echo "  normalise  Build WNSC composites (Steps 4-5)"
	@echo "  lulc       Aggregate to 30 m and identify transitions (Step 6)"
	@echo "  match      Build SRS and matched pairs (Step 7)"
	@echo "  attribute  Compute LUTHI + bootstrap + placebo + SHAP (Steps 8-9)"
	@echo "  hipi       Heat improvement priority map (Step 10)"
	@echo "  figures    Render Fig 1-8 and tables (Step 12)"
	@echo "  all        Run everything in order"
	@echo "  clean      Remove outputs/ and figures/ contents"

env:
	mamba env create -f env/environment.yml || conda env create -f env/environment.yml

auth:
	earthengine authenticate
	-earthaccess login

ingest:
	luthea ingest-dw
	luthea ingest-lst

normalise:
	luthea ingest-jma
	luthea select-days
	luthea normalise-lst
	luthea wnsc

lulc:
	luthea aggregate-lulc
	luthea transitions

match:
	luthea match

attribute:
	luthea luthi
	luthea bootstrap
	luthea placebo
	luthea ml-attribute

hipi:
	luthea hipi

figures:
	luthea figures

all: ingest normalise lulc match attribute hipi figures

clean:
	find outputs -type f ! -name '.gitkeep' -delete
	find figures -type f ! -name '.gitkeep' -delete
	find tables  -type f ! -name '.gitkeep' -delete
