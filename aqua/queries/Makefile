EPSTOPDF=epstopdf

all: queries

queries: queries.py
	python queries.py
	for eps in *.eps; do \
		make `basename $$eps .eps`.pdf ; \
	done

%.pdf: %.eps
	cat $< | $(EPSTOPDF) --nocompress --filter > `basename $< .eps`.pdf

clean:
	rm -vf *~ *.png *.ps *.eps *.pdf *.pyc
