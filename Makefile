check:
	python3 git_bigfile_tests.py 

test_%:
	python3 git_bigfile_tests.py $@ -v -k

t_%:
	python3 git_bigfile_tests.py $@ -vv -k

d_%:
	python3 git_bigfile_tests.py $@ -vv -k
