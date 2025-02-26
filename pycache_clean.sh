# pyclean command to clear all python cache in a directory
# source: https://stackoverflow.com/questions/28991015/python3-project-remove-pycache-folders-and-pyc-files
# sudo bash pycache_clean.sh


# in .bash_profile / .bash_rc etc put:
pyclean () {
    find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
}


# Now to delete all python cache in a directory do:
pyclean