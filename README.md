## naturejobs_scraper.py
A Python scraper for [nature.com's job website](http://www.naturejobs.com).
Licensed under GPL v3 (see COPYING).
***
### Rationale
Nature's job website is a little frustrating to use. First, there's no option of setting the number of jobs per page. This means clicking through dozens of pages to see those posted, e.g. in a week. Secondly, although you can set inclusive filters, I would prefer by default to be able to quickly skim through all the jobs posted excluding those that are of no interest to me.

So, I wrote this script. It creates a HTML table which contains jobs posted on the website and can filter out jobs by title, employer or location.
***
### Usage examples
Run njs.py from the command line. It outputs a HTML file in the same directory.

The last page number to process is the only required argument, e.g. `-lp 10` will process the first ten pages of the site. If you browse the [site](http://www.nature.com/naturejobs/science/jobs), it will show you the highest page number, or you can enter a very large number, e.g. `-lp 9999` and the script will stop once it reaches the final page.

The default output filename is autogenerated from current date and time, unless a filename is specified with `-o filename`.

`njs.py -h`  
Show help.  
`njs.py -o jobs.html -lp 30`  
Save jobs from first thirty pages to jobs.html. 

Job titles, employers and locations can be specified to be ignored using the options `-it`, `-ie` and `-il` respectively; any jobs matching these terms will be not be included in the output HTML. Multiple entries for each option should have a space between, spaces in the terms should be replaced with underscores.

`njs.py -o remove-phd-jobs.html -it PhD`  
Any jobs containing __PhD__ in the title will not be included in the HTML.  
`njs.py -o remove-more-phd-jobs.html -it PhD Ph.D`  
Any jobs containing __PhD__ or __Ph.D__ in the title will not be included in the HTML.  
`njs.py -o filter-employer.html -ie Black_Mesa_Research_Facility`  
Any jobs with __Black Mesa Research Facility__ listed as an employer will not be included in the HTML.  
`njs.py -lp 100 -o not-on-the-moon.html -il Moon`  
Any jobs on the __Moon__ will not be included in the HTML. Pages up to and including page 100 will be processed.  

These options can be combined.  
`njs.py -o multiple-filters.html -il Moon -it PhD Ph.D -ie Black_Mesa_Research_Facility`
***
### Dependencies and issues
* Tested on Python 2.7.3 on Windows (Windows 7 64-bit) and Linux (Raspbian).
* Requires [BeautifulSoup 4.1.3](http://www.crummy.com/software/BeautifulSoup/)
* It does handle international characters in job titles, employers and locations, but, if running on a Linux machine via ssh, make sure that the character set of the ssh client matches that of the shell. (When testing using PuTTY on Windows to connect to a Raspberry Pi, I spent a long time trying to debug the wrong characters being sent to the script until I realised it was PuTTY's remote character set that didn't match the UTF-8 locale setting of bash.) 
