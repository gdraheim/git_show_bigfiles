check:
	python3 git-bigfile-tests.py 

test_%:
	python3 git-bigfile-tests.py $@ -v -k

t_%:
	python3 git-bigfile-tests.py $@ -vv -k

d_%:
	python3 git-bigfile-tests.py $@ -vv -k
