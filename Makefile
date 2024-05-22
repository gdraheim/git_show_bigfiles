check:
	python3 git-bigfile-tests.py 

test_%:
	python3 git-bigfile-tests.py $@ -v