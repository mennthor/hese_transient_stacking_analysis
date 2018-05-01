TEXOPTS = --output-directory=build --lualatex
TEXINPUT = header.tex titlepage.tex

TARGET = main

all: $(TARGET).pdf

$(TARGET).pdf: $(TEXINPUT) $(TARGET).tex | build
	latexmk $(TEXOPTS) $(TARGET).tex

preview: ${TEXINPUT} $(TARGET).tex | build
	latexmk $(TEXOPTS) -pvc $(TARGET).tex


build:
	mkdir -p build

clean:
	rm -rf build
