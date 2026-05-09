TEX := vllm-hust-introduction.tex
OUTDIR := build
PDF := $(OUTDIR)/vllm-hust-introduction.pdf

.PHONY: all clean

all: $(PDF)

$(PDF): $(TEX)
	mkdir -p $(OUTDIR)
	tectonic --keep-logs --keep-intermediates --outdir $(OUTDIR) $(TEX)

clean:
	rm -rf $(OUTDIR)