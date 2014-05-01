SHELL = /bin/sh

CURL ?= curl
UNZIP ?= unzip
FLIP ?= flip
PYTHON ?= python

DESTDIR = data

TWORPORA = $(PYTHON) -m tworpora
TWORPORA_DATA = $(DESTDIR)
export TWORPORA_DATA

STS_PATH = $(DESTDIR)/sts
STS_ZIP = $(STS_PATH).zip
STS_TEST_FILE = $(STS_PATH)-test.tsv
STS_GOLD_PATH = $(DESTDIR)/sts-gold
STS_GOLD_ZIP = $(STS_GOLD_PATH).zip
STS_GOLD_FILE = $(STS_GOLD_PATH).tsv
HCR_PATH = $(DESTDIR)/hcr
HCR_FILE = $(HCR_PATH).tsv
OMD_PATH = $(DESTDIR)/omd
OMD_FILE = $(OMD_PATH).tsv
SENTISTRENGTH_PATH = $(DESTDIR)/sentistrength
SENTISTRENGTH_ZIP = $(SENTISTRENGTH_PATH).zip
SENTISTRENGTH_FILE = $(SENTISTRENGTH_PATH).tsv
SANDERS_PATH = $(DESTDIR)/sanders
SANDERS_ZIP = $(SANDERS_PATH).zip
SANDERS_FILE = $(SANDERS_PATH).tsv
SEMEVAL2013_PATH = $(DESTDIR)/semeval2013
SEMEVAL2013_FILE = $(SEMEVAL2013_PATH).tsv

PACKAGES = sts-test sts-gold hcr omd sentistrength sanders semeval2013

all: packages

requirements:
	pip install -r requirements.txt

packages: $(PACKAGES)
sts-test: $(STS_TEST_FILE)
$(STS_TEST_FILE):
	$(TWORPORA) sts_test > $@
sts-gold: $(STS_GOLD_FILE)
$(STS_GOLD_FILE):
	$(TWORPORA) sts_gold > $@
hcr: $(HCR_FILE)
$(HCR_FILE):
	$(TWORPORA) hcr > $@
omd: $(OMD_FILE)
$(OMD_FILE):
	$(TWORPORA) omd > $@
sentistrength: $(SENTISTRENGTH_FILE)
$(SENTISTRENGTH_FILE):
	$(TWORPORA) sentistrength > $@
sanders: $(SANDERS_FILE)
$(SANDERS_FILE):
	$(TWORPORA) sanders > $@
semeval2013: $(SEMEVAL2013_FILE)
$(SEMEVAL2013_FILE):
	$(TWORPORA) semeval2013 > $@

clean:
	-rm -rf -- $(DESTDIR)/*.tsv \
		$(STS_PATH) \
		$(STS_GOLD_PATH) \
		$(SENTISTRENGTH_PATH) \
		$(SANDERS_PATH)

clobber: clean
	-rm -rf -- $(DESTDIR)/*.db \
		$(STS_ZIP) \
		$(STS_GOLD_ZIP) \
		$(HCR_PATH) \
		$(OMD_PATH) \
		$(SENTISTRENGTH_ZIP) \
		$(SANDERS_ZIP) \
		$(SEMEVAL2013_PATH)

.PHONY: all requirements packages $(PACKAGES) clean clobber
.DELETE_ON_ERROR:
