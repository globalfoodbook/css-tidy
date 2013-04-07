#!/usr/bin/python

"""
Reads a .csv file generated by the firefox "Dust-me Selectors" extension
(https://addons.mozilla.org/en-US/firefox/addon/dust-me-selectors/)
and generates the cleaned up .css files in the current working directory.
"""

import argparse
import sys
import cssutils
import csv
import os

STYLE_OPTIONS = {
  "indent": "  ",
  "keepAllProperties": False,
  "keepUnknownRules": False,
  "omitLastSemicolon": False,
  "indentClosingBrace": False,
  "keepComments": True,
}

class Stylesheet(object):
  def __init__(self, uri):
    self.uri = uri
    self.blacklist = set()

def main():
  argparser = argparse.ArgumentParser(description=__doc__)
  argparser.add_argument("csvfile", metavar="CSV-FILE", nargs=1, help="CSS file to parse")
  argparser.add_argument("--keep-comments", dest="comments", action="store_false",
                         default=True, help="Keep comments in generatd output files?")
  args = argparser.parse_args()
  style_options = STYLE_OPTIONS
  style_options["keepComments"] = args.comments

  stylesheets = []
  reader = csv.reader(open(args.csvfile[0]))
  for line, columns in enumerate(reader):
    if line == 0:
      for column in columns:
        stylesheets.append(Stylesheet(column))
    if line == 1:
      continue

    for stylen, column in enumerate(columns):
      stylesheets[stylen].blacklist.add(column)

  cssparser = cssutils.CSSParser()
  for stylesheet in stylesheets:
    print "Working on", stylesheet.uri
    css = cssparser.parseUrl(stylesheet.uri, validate=False)
    output = cssutils.css.CSSStyleSheet()
    for key, value in style_options.iteritems():
      output.setSerializerPref(key, value)
    for rule in css:
      if rule.type != rule.STYLE_RULE:
        output.add(rule)
        continue
      selectors = cssutils.css.SelectorList(parentRule=rule.selectorList.parentRule)
      for selector in rule.selectorList:
        if selector.selectorText in stylesheet.blacklist:
          print "BLACKLISTED", selector.selectorText
          continue
        selectors.appendSelector(selector)

      if not selectors.length:
        continue

      newrule = cssutils.css.CSSStyleRule(
          style=rule.style, parentRule=rule.parentRule,
          parentStyleSheet=rule.parentStyleSheet)
      newrule.selectorList = selectors
      output.add(newrule)

    outputfile = os.path.basename(stylesheet.uri)
    print "Saving stripped stylesheet in", outputfile
    open(outputfile, "w").write(output.cssText)

if __name__ == "__main__":
  sys.exit(main())
