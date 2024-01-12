"""Test if fileinput.input() in add-license-headers decodes bad characters."""
# This intentionally does not have a header, so we can test the
# license header is added in test_reuse.py - test_bad_chars()
print("ÞĀĂĄĆĈĊČĎĐĒĔĖĘĚĜĞĠĢĤĦĨĪĬĮİĲĴ")
