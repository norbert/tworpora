SHELL = /bin/sh

CURL ?= curl
UNZIP ?= unzip
FLIP ?= flip
PYTHON ?= python
TWORPORA = $(PYTHON) -m tworpora

DESTDIR = data

STS_PATH = $(DESTDIR)/sts
STS_ZIP = $(STS_PATH).zip
STS_TEST_FILE = $(STS_PATH)-test.tsv
STS_GOLD_PATH = $(DESTDIR)/sts-gold
STS_GOLD_ZIP = $(STS_GOLD_PATH).zip
STS_GOLD_FILE = $(STS_GOLD_PATH).tsv
HCR_PATH = $(DESTDIR)/hcr
HCR_FILE = $(HCR_PATH).tsv
OMD_PATH = $(DESTDIR)/omd
OMD_SOURCE = $(OMD_PATH)/debate08_sentiment_tweets.tsv
OMD_FILE = $(OMD_PATH).tsv
SENTISTRENGTH_PATH = $(DESTDIR)/sentistrength
SENTISTRENGTH_ZIP = $(SENTISTRENGTH_PATH).zip
SENTISTRENGTH_FILE = $(SENTISTRENGTH_PATH).tsv
SANDERS_PATH = $(DESTDIR)/sanders
SANDERS_ZIP = $(SANDERS_PATH).zip
SANDERS_FILE = $(SANDERS_PATH).tsv
SEMEVAL2013_PATH = $(DESTDIR)/semeval2013
SEMEVAL2013_FILES = tweeti-a.dev.dist.tsv tweeti-a.dist.tsv tweeti-b.dev.dist.tsv tweeti-b.dist.tsv
SEMEVAL2013_FILE = $(SEMEVAL2013_PATH).tsv

PACKAGES = sts_test sts_gold hcr omd sentistrength sanders semeval2013

all: packages

requirements:
	pip install -r requirements.txt

packages: $(PACKAGES)
sts_test: $(STS_TEST_FILE)
$(STS_TEST_FILE): $(STS_PATH)
	$(TWORPORA) sts_test > $@
$(STS_ZIP):
	$(CURL) -s -o $@ http://cs.stanford.edu/people/alecmgo/trainingandtestdata.zip
$(STS_PATH): $(STS_ZIP)
	$(UNZIP) -q $< testdata.manual.2009.06.14.csv -d $@
sts_gold: $(STS_GOLD_FILE)
$(STS_GOLD_FILE): $(STS_GOLD_PATH)
	$(TWORPORA) sts_gold > $@
$(STS_GOLD_ZIP):
	$(CURL) -s -o $@ http://tweenator.com/download/sts_gold_v03.zip
$(STS_GOLD_PATH): $(STS_GOLD_ZIP)
	$(UNZIP) -q $< sts_gold_tweet.csv -d $@
hcr: $(HCR_FILE)
$(HCR_FILE): $(HCR_PATH)
	$(TWORPORA) hcr > $@
$(HCR_PATH):
	mkdir -p $@
	$(CURL) -s -o $@/hcr-dev.csv https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/hcr/dev/orig/hcr-dev.csv
	$(CURL) -s -o $@/hcr-test.csv https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/hcr/test/orig/hcr-test.csv
	$(CURL) -s -o $@/hcr-train.csv https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/hcr/train/orig/hcr-train.csv
omd: $(OMD_FILE)
$(OMD_FILE): $(OMD_SOURCE)
	$(TWORPORA) omd > $@
$(OMD_SOURCE):
	mkdir -p $(@D)
	$(CURL) -s -o $@ https://bitbucket.org/speriosu/updown/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16/data/shamma/orig/debate08_sentiment_tweets.tsv
	$(FLIP) -u $@
sentistrength: $(SENTISTRENGTH_FILE)
$(SENTISTRENGTH_FILE): $(SENTISTRENGTH_PATH)
	$(TWORPORA) sentistrength > $@
$(SENTISTRENGTH_ZIP):
	$(CURL) -s -o $@ http://sentistrength.wlv.ac.uk/documentation/6humanCodedDataSets.zip
$(SENTISTRENGTH_PATH): $(SENTISTRENGTH_ZIP)
	$(UNZIP) -q $< twitter4242.txt -d $@
sanders: $(SANDERS_FILE)
$(SANDERS_FILE): $(SANDERS_PATH)
	$(TWORPORA) sanders > $@
$(SANDERS_ZIP):
	$(CURL) -s -o $@ http://www.sananalytics.com/lab/twitter-sentiment/sanders-twitter-0.2.zip
$(SANDERS_PATH): $(SANDERS_ZIP)
	$(UNZIP) -q -j $< sanders-twitter-0.2/corpus.csv -d $@
semeval2013: $(SEMEVAL2013_FILE)
$(SEMEVAL2013_FILE): $(SEMEVAL2013_PATH)
	$(TWORPORA) semeval2013 > $@
$(SEMEVAL2013_PATH):
	mkdir -p $@
	for file in $(SEMEVAL2013_FILES) ; do\
		$(CURL) -s -o $@/$$file http://www.cs.york.ac.uk/semeval-2013/task2/data/uploads/datasets/$$file ;\
	done

clean:
	-rm -rf -- $(DESTDIR)/*.tsv
clobber: clean
	-rm -rf -- $(DESTDIR)/*.db \
		$(STS_ZIP) $(STS_PATH) \
		$(STS_GOLD_ZIP) $(STS_GOLD_PATH) \
		$(HCR_PATH) \
		$(OMD_PATH) \
		$(SENTISTRENGTH_ZIP) $(SENTISTRENGTH_PATH) \
		$(SANDERS_ZIP) $(SANDERS_PATH) \
		$(SEMEVAL2013_PATH)

.PHONY: all requirements packages $(PACKAGES) clean clobber
.DELETE_ON_ERROR:
