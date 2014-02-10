SHELL = /bin/sh

CURL ?= curl
UNZIP ?= unzip
FLIP ?= flip

DESTDIR = data

STS_PATH = $(DESTDIR)/sts
STS_ZIP = $(STS_PATH).zip
HCR_PATH = $(DESTDIR)/hcr
OMD_PATH = $(DESTDIR)/omd
OMD_FILE = $(OMD_PATH)/debate08_sentiment_tweets.tsv
SENTISTRENGTH_PATH = $(DESTDIR)/sentistrength
SENTISTRENGTH_ZIP = $(SENTISTRENGTH_PATH).zip
SANDERS_PATH = $(DESTDIR)/sanders
SANDERS_ZIP = $(SANDERS_PATH).zip
SEMEVAL2013_PATH = $(DESTDIR)/semeval2013
SEMEVAL2013_FILES = tweeti-a.dev.dist.tsv tweeti-a.dist.tsv tweeti-b.dev.dist.tsv tweeti-b.dist.tsv

PACKAGES = sts hcr omd sentistrength sanders semeval2013

all: packages

packages: $(PACKAGES)
sts: $(STS_PATH)
$(STS_ZIP):
	$(CURL) -s -o $@ http://cs.stanford.edu/people/alecmgo/trainingandtestdata.zip
$(STS_PATH): $(STS_ZIP)
	$(UNZIP) -q $< testdata.manual.2009.06.14.csv -d $@
hcr: $(HCR_PATH)
$(HCR_PATH):
	mkdir -p $@
	$(CURL) -s -o $@/hcr-dev.csv https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/hcr/dev/orig/hcr-dev.csv
	$(CURL) -s -o $@/hcr-test.csv https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/hcr/test/orig/hcr-test.csv
	$(CURL) -s -o $@/hcr-train.csv https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/hcr/train/orig/hcr-train.csv
omd: $(OMD_FILE)
$(OMD_FILE):
	mkdir -p $(@D)
	$(CURL) -s -o $@ https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/shamma/orig/debate08_sentiment_tweets.tsv
	$(FLIP) -u $@
sentistrength: $(SENTISTRENGTH_PATH)
$(SENTISTRENGTH_ZIP):
	$(CURL) -s -o $@ http://sentistrength.wlv.ac.uk/documentation/6humanCodedDataSets.zip
$(SENTISTRENGTH_PATH): $(SENTISTRENGTH_ZIP)
	$(UNZIP) -q $< twitter4242.txt -d $@
sanders: $(SANDERS_PATH)
$(SANDERS_ZIP):
	$(CURL) -s -o $@ http://www.sananalytics.com/lab/twitter-sentiment/sanders-twitter-0.2.zip
$(SANDERS_PATH): $(SANDERS_ZIP)
	$(UNZIP) -q -j $< sanders-twitter-0.2/corpus.csv -d $@
semeval2013: $(SEMEVAL2013_PATH)
$(SEMEVAL2013_PATH):
	mkdir -p $@
	for file in $(SEMEVAL2013_FILES) ; do\
		$(CURL) -s -o $@/$$file http://www.cs.york.ac.uk/semeval-2013/task2/data/uploads/datasets/$$file ;\
	done

clean:
	-rm -rf -- \
		$(STS_PATH) \
		$(SENTISTRENGTH_PATH) \
		$(SANDERS_PATH)
clobber: clean
	-rm -rf -- \
		$(STS_ZIP) \
		$(HCR_PATH) \
		$(OMD_PATH) \
		$(SENTISTRENGTH_ZIP) \
		$(SANDERS_ZIP) \
		$(SEMEVAL2013_PATH)

.PHONY: all packages $(PACKAGES) clean clobber
.DELETE_ON_ERROR:
