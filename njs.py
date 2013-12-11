#!/usr/bin/env python

# naturejobs_scraper: Scrapes nature.com's job website; writes jobs to HTML
# Copyright 2013 Steven Maude

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Features implemented:
# handle unicode keywords; tested on Linux
# gzip encoding
# better command line parameter handling with argparse

# Improvements to make
# less clunky keyword checking; put into keyword_check(current_word, ign_words)
# more thorough exception handling and maybe more testing
# ...though it works :)

# Updated June 2013: make it work again, handle rare 1 pixel web bugs wrecking
# layout of table
from __future__ import print_function
from contextlib import closing
from StringIO import StringIO
from bs4 import BeautifulSoup
import argparse
import datetime
import gzip
import urllib2
import random
import time
import sys

def get_arguments():
    """
    Returns last_page_no, filename, and titles, employers, locations to ignore
    from command line arguments. last_page_no is mandatory (int). Filename
    is set to default of current date and time if not present. Jobs, titles and
    employers.
    """
    prog_desc = ("Scrapes naturejobs website and "
                 "writes job details into HTML table")
    underscore_strg = "replace spaces with underscores"

    # get date and time
    # see http://www.saltycrane.com/blog/2008/06/how-to-get-current-date-and-time-in/
    current_time = datetime.datetime.now()
    time_string = current_time.strftime("%Y-%m-%d_%H%M%S")

    # *** friendlier error messages? rather than e.g. invalid int value
    parser = argparse.ArgumentParser(description = prog_desc)
    parser.add_argument('-o', help = "HTML output file; defaults to date_time",
                        default = time_string + '.html',
                        metavar = 'HTML_output_filename')
    parser.add_argument('-lp',
                        help = "last page number to download",
                        #default = 999
                        metavar = 'page_number',
                        required = True,
                        type = int)
    parser.add_argument("-it",
                        help = ("job titles to ignore; " + underscore_strg),
                        nargs = '*',
                        metavar = 'job_title')
    parser.add_argument("-ie",
                        help = ("employers to ignore; " + underscore_strg),
                        nargs = '*',
                        metavar = 'employer')
    parser.add_argument("-il",
                        help = ("locations to ignore; " + underscore_strg),
                        nargs = '*',
                        metavar = 'location')

    args = parser.parse_args()
    # check if titles, employers, locations are present
    # if they are, decode the string and replace underscores with spaces
    # if not, replace with empty lists
    if args.it != None:
        titles = tidy_list(args.it)
    else:
        titles = []

    if args.ie != None:
        employers = tidy_list(args.ie)
    else:
        employers = []

    if args.il != None:
        locations = tidy_list(args.il)
    else:
        locations = []

    return args.lp, args.o, titles, employers, locations

def tidy_list(arg_list):
    """
    Take a list of arguments, e.g. list of employers, return a new list of
    decoded strings and with underscores replaced with spaces.
    """
    tidied_list = []

    for item in arg_list:
        # decode string
        tidied_string = item.decode(sys.getfilesystemencoding())
        # add to new list with underscores replaced by spaces
        tidied_list.append(tidied_string.replace('_', ' '))

    return tidied_list

def get_last_page_number(soup):
    """
    Takes soup of first page, and returns the highest page number found as
    an integer.
    """
    # find last page number
    last_page_number = 0

    for a in soup.findAll('a'):
        if 'href="/naturejobs/science/jobs?page=' in str(a):
            try:
                page_number_found = int(a.get_text())
                if page_number_found > last_page_number:
                    last_page_number = page_number_found
            except ValueError:
                # handle >
                pass

    return last_page_number

def open_webpage(url):
    """
    Opens webpage (requests gzip if possible) and returns soup.
    Exits program if page opening fails.
    """
    print("Opening web page: " + url)
    # get html
    # code based on http://stackoverflow.com/questions/3947120/
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-Encoding', 'gzip')
        response = urllib2.urlopen(request)
        # if we have a gzipped page, read contents as gzip
        if response.info().get('Content-Encoding') == 'gzip':
            # see http://code.activestate.com/recipes/576650-with-statement-for-stringio/
            # can use with statement for BytesIO in Python 3
            with closing(StringIO(response.read())) as sio:
                f = gzip.GzipFile(fileobj=sio)
                html = f.read()
        # otherwise just read contents directly
        else:
            html = response.read()
        soup = BeautifulSoup(html)
    # check what exception to handle here rather than general except
    except:
        print("Error opening web page.")
        print("Check network connection, or page may be down.")
        raise
        sys.exit()
    finally:
        response.close()

    return soup

def process_jobs_in_pages(URL, last_page, fname, to_ignore):
    """
    Iterates over Nature Jobs web pages from page 1 to last_page. Writes each
    job out as a HTML row, subject to it not having a title or employer that
    should be ignored.
    """
    ign_employers = to_ignore['emp']
    ign_titles = to_ignore['titles']
    ign_loc = to_ignore['loc']

    # need to iterate over each page on site
    for page_num in range(1, last_page + 1):
        # introduce random time delay before grabbing pages
        # to be polite, and to avoid any unwanted client banning
        time.sleep(random.uniform(3,8))
        # gracefully handle times when the website plays up...
        # try a fixed number of times; if successful, exit while loop
        num_tries = 10
        page_accessed = False
        ##while (num_tries > 0) and not page_accessed:
        while not page_accessed:
            try:
                temp_soup = open_webpage(URL + str(page_num))
##                li = temp_soup.find('li', \
##                                    class_='job ')
##                print(li)
##                # remove the navigable strings from the results;
##                # these have len == 1
##                temp_list = [thing for thing in li.children if len(thing) > 1]
                another_temp = temp_soup.find('ul', class_='jobs-list regular')
                temp_list = another_temp.findAll('div', class_='job-details')

            # *** need to figure out which exception occurs here
            # could try pointing temp_soup to open wrong webpage and see
            except:
                # reduce number of tries, pause, then try again
                num_tries -= 1
                # if run out of tries, exit
                if num_tries == 0:
                    sys.exit("Tries exceeded. Naturejobs may be down.")
                else:
                    print("Problem accessing website. Retrying...")
                    time.sleep(random.uniform(5,10))
            else:
                page_accessed = True

        # go through jobs in a page
        for each_job in temp_list:
            (job_employer, job_title, job_locale, job_desc, job_age) = [u''] * 5
            job_link = u'http://www.nature.com'
            job_wanted = True
            # could do keyword ignoring for descriptions too...
            try:
                job_employer = each_job.find('li', class_='employer'\
                                            ).get_text().strip()
                # check if employer matches one of the keywords to ignore
                for employer in ign_employers:
                    if job_employer.lower().find(employer.lower()) != -1:
                        job_wanted = False
                        break
            # get AttributeError if there is no text in the employer section
            except AttributeError:
                pass

            # *** Include this continue check after every search?
            # if we have an employer that we don't want, go to the next job
            # skipping this one
            #if not job_wanted:
            #    continue

            try:
                job_title = each_job.find('h3').get_text().strip()
                # check if title matches one of the keywords to ignore
                for title in ign_titles:
                    if job_title.lower().find(title.lower()) != -1:
                        job_wanted = False
                        break

            except AttributeError:
                pass

            try:
                job_link = 'http://www.nature.com' + each_job.a['href']
            except (TypeError, AttributeError):
                pass

            try:
                job_locale = each_job.find('li', class_='locale'\
                                            ).get_text().strip()
                for place in ign_loc:
                    if job_locale.lower().find(place.lower()) != -1:
                        job_wanted = False
                        break

            except AttributeError:
                pass

            try:
                job_desc = each_job.find('p', class_='job-desc'\
                                            ).get_text().strip()
            except AttributeError:
                pass

            try:
                job_age = each_job.find('li', class_='when').get_text().strip()
            except AttributeError:
                pass

            # if we have an employer that we don't want, go to the next job
            # skipping this one
            if not job_wanted:
                continue

            job_info = {'title': job_title, 'employer': job_employer, \
                        'locale': job_locale, 'age': job_age, \
                        'desc': job_desc, 'link': job_link}
            # write out job info to HTML table row
            write_job_info_to_html(job_info, fname)

def write_table_opening_html(fname):
    """
    Writes opening table HTML to file. Overwrites existing file.
    """
    with open(fname, 'w') as f:
        # write opening HTML
        f.write('<!DOCTYPE html>\n')
        f.write('<html>\n')
        f.write('<head>\n')
        f.write('<meta charset="UTF-8">')
        f.write('</head>\n')
        f.write('<body>\n\n')
        f.write('<table border="1">\n')

        # set column widths? e.g.
        # same indent as <tr>
        #  <colgroup>
        #    <col span="1" style="width: 15%;">
        #    <col span="1" style="width: 70%;">
        #    <col span="1" style="width: 15%;">
        #  </colgroup>

        # write table headers
        f.write('  <tr>\n')
        f.write('    <th>Employer</th>\n')
        f.write('    <th>Location</th>\n')
        f.write('    <th>Time posted</th>\n')
        f.write('    <th>Title</th>\n')
        f.write('    <th>Description</th>\n')
        f.write('  </tr>\n')

def write_end_html(fname, to_ignore):
    """
    Writes table closing and end HTML to file, including date/time and
    the keyword filters used.
    """
    ign_employers = to_ignore['emp']
    ign_titles = to_ignore['titles']
    ign_loc = to_ignore['loc']

    with open(fname, 'a') as f:
        f.write('</table>')
        f.write('\n\n')
        # combine each
        f.write('<p style="font-size:80%">\n')
        # *** could write a function for each of these
        if len(ign_employers) > 0:
            f.write('Ignored employers:')
            emp_string = ' '
            for emp in ign_employers:
                emp_string += emp + ', '
            # remove trailing comma,space
            emp_string = emp_string[:-2]
            f.write(emp_string.encode("UTF-8"))
            f.write('<br>\n')

        if len(ign_titles) > 0:
            f.write('Ignored titles:')
            title_string = ' '
            for title in ign_titles:
                title_string += title + ', '
            title_string = title_string[:-2]
            f.write(title_string.encode("UTF-8"))
            f.write('<br>\n')

        if len(ign_loc) > 0:
            f.write('Ignored titles:')
            loc_string = ' '
            for place in ign_loc:
                loc_string += place + ', '
            loc_string = loc_string[:-2]
            f.write(loc_string.encode("UTF-8"))
            f.write('<br>\n')

        # write date/time
        struct_time = time.localtime()
        # code from http://stackoverflow.com/questions/1697815/
        # is *args here necessary?
        date_time_created = datetime.datetime(*struct_time[:6])
        f.write('Generated ' + str(date_time_created) + '\n')
        f.write('</p>')
        f.write('\n\n</body>\n</html>')

def write_job_info_to_html(job_info, fname):
    """
    Writes a job description as a HTML table row. Appends to existing file.
    """
    # encode unicode text from HTML as strings
    # could pass these as a dict, then create copy of encoded strings
    title_coded = job_info['title'].encode("UTF-8")
    employer_coded = job_info['employer'].encode("UTF-8")
    location_coded = job_info['locale'].encode("UTF-8")
    posted_coded = job_info['age'].encode("UTF-8")
    desc_coded = job_info['desc'].encode("UTF-8")
    # fix for stupid 1 pixel doubleclick.net web bugs from Life Technologies :/
    # it causes the <td> tag to not close as expected
    # the next <td> is after the name of the next job
    # name of next job ends up in description of previous job
    # rest of info of next job ends up in a phantom column after the description
    # as the next <tr> is within quotes...

    # doesn't help that tag isn't closed, so can't easily remove it
    # try splitting at <img_src
    desc_coded = desc_coded.split('<img src')[0]
    link_coded = job_info['link'].encode("UTF-8")

    with open(fname, 'a') as f:
        f.write('  <tr>\n')
        # can use  target="_blank" after link to force new window
        f.write('    <td>' + employer_coded + '</td>\n')
        f.write('    <td>' + location_coded + '</td>\n')
        f.write('    <td>' + posted_coded + '</td>\n')
        f.write('    <td><a href="' + link_coded +
                '">' + title_coded + '</td>\n')
        f.write('    <td>' + desc_coded + '</td>\n')
        f.write('  </tr>\n')

def main():
    """
    Opens Nature's job website, finds the last page number, iterates from the
    first page to the last page (user-specified), then extracts information
    from each job to a HTML table (user-specified output file).
    """
    # handle all the keywords to be ignored in a dictionary
    to_ignore = {'titles': [], 'emp': [], 'loc': []}
    (last_page_to_process, html_filename, to_ignore['titles'],
     to_ignore['emp'], to_ignore['loc']) = get_arguments()

    # pages generated by nature_url + extension + number from 1 (first page)
    # to last page
    nature_url = 'http://www.nature.com/naturejobs/science/jobs'
    extension = '?page='

    # display ignored employers and titles
    # *** could write function here
    if len(to_ignore['emp']) > 0:
        print("Ignoring employers:")
        for emp in to_ignore['emp']:
            print(emp)

    if len(to_ignore['titles']) > 0:
        print("Ignoring phrases in titles:")
        for title in to_ignore['titles']:
            print(title)

    if len(to_ignore['loc']) > 0:
        print("Ignoring places:")
        for place in to_ignore['loc']:
            print(place)

    # get last page number
    soup = open_webpage(nature_url)
    last_page_number = get_last_page_number(soup)
    print("Finding last available page of site...", end = ' ')
    print("last page available is", last_page_number)
    # check last page number requested by user is not greater than possible
    if last_page_to_process > last_page_number:
        last_page_to_process = last_page_number
    print("Last page to process will be", last_page_to_process)
    print("Processing pages...")
    # process jobs and write html
    try:
        write_table_opening_html(html_filename)
        process_jobs_in_pages(nature_url + extension, \
                                last_page_to_process, html_filename, to_ignore)
        # *** could maybe return True or False from process_jobs_in_pages()
        # to determine whether we should write "No jobs found".?
        write_end_html(html_filename, to_ignore)
    except IOError:
        print("Error writing to file.")

    print("Done!")

if __name__ == '__main__':
    main()
