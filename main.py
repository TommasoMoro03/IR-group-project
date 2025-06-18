import sys
from crawling import crawler
from retrieving import retriever

#check the command line arguments for --new command
new = "--new" in sys.argv

# execute crawling
crawler.main(new=new)

# execute retrieving
retriever.main()