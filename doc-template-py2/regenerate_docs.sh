# run this in docs/ dir

# to build documentation you should:
# 1) install sphinx
# 2) make sure all dependencies for current package are available (sphinx imports modules, so dependencies are imported too)

sphinx-apidoc -o source ../
make html
