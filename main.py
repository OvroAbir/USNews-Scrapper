import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import json
import csv
from argparse import ArgumentParser
from urllib import parse
import os
import shutil
import tablib
from tqdm import tqdm


#Global Variables
args = None
temp_folder = "./temp"
output_headers = []
data_tablib = None


class GradSchool:
    def __init__(self, name, state, city, rank, is_tied, score, school_url):
        self.name = name
        self.state = state
        self.city = city
        
        try:
            self.rank = int(rank)
        except (ValueError, TypeError) as e:
            self.rank = rank
    
        self.is_tied = is_tied
        
        try:
            self.score = float(score)
        except (ValueError, TypeError) as e:
            self.score = score

        self.school_url = school_url

    
    @classmethod
    def getFromJSON(cls, json_data):
        name = state = city = rank = is_tied = score = url = None
        
        try:        
            name = json_data["name"]
        except KeyError:
            pass

        try:
            state = json_data["state"]
        except KeyError:
            pass
        
        try:
            city = json_data["city"]
        except KeyError:
            pass
            

        try:
            rank = json_data["ranking"]["display_rank"]
        except KeyError:
            pass
        
        try:
            is_tied = json_data["ranking"]["is_tied"]
        except KeyError:
            pass
        
        try:
            score = json_data["schoolData"]["c_avg_acad_rep_score"]
        except KeyError:
            pass
        
        try:
            url = json_data["url"]
        except KeyError:
            pass

        return cls(name, state, city, rank, is_tied, score, url)

    def __iter__(self):
        yield self.rank
        yield self.name
        yield self.state
        yield self.city
        #yield self.is_tied
        yield self.score
        yield self.school_url

    def __str__(self):
        return "name : {} \nstate : {} \ncity : {} \nrank : {} \nis tied : {} \nscore : {} \nschool url : {}".format(self.name, self.state, self.city, self.rank, self.is_tied, self.score, self.school_url)


def modifyparser(parser):
    defaulturl = "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings"
    default_output_file_name = "usnews"
    default_pause_time = 2
    default_start_page = 1
    default_end_page = 100

    parser.add_argument("-u", "--url", help="The address to collect data from. Put the URL within qoutes i.e. \" or \'", dest="url", default=defaulturl, type=str)
    parser.add_argument("-o", help="The output file name without extension", dest="outputfilename", default=default_output_file_name)
    parser.add_argument("-p", "--pause", help="The pause time between loading pages from usnews", dest="pausetime", default=default_pause_time)
    parser.add_argument("--from", help="The page number from which the scrapper starts working", dest="startpage", default=default_start_page)
    parser.add_argument("--to", help="The page number to which the scrapper works", dest="endpage", default=default_end_page)
    
def parseargs():
    parser = ArgumentParser(description="Collects data from usnews and generates excel file")
    modifyparser(parser)
    args = parser.parse_args()

    return args
'''
def extract_parameters_from_url(url):
    location_params = {}
    parse_results = parse.urlsplit(url)
    
    locations = parse_results.path.split("/")[2:]
    program = locations[0]
    if program != "search":
        location_params["program"] = program

    try:
        specialty = locations[1][:locations[1].rfind("-")]
        location_params["speciality"] = specialty
    except:
        pass

    location_params["_page"] = "dummy"

    querie_params = dict(parse.parse_qsl(parse_results.query))    
    params = {**location_params, **querie_params}

    return params
'''
def extract_parameters_from_url(url):
    parse_results = parse.urlsplit(url)
    
    locations = parse_results.path.split("/")[2:]
    program = locations[0]
    specialty = locations[1][:locations[1].rfind("-")]
    location_params = {
        "program": program,
        "specialty": specialty,
        "_page": "dummy"
    }
    
    querie_params = dict(parse.parse_qsl(parse_results.query))    
    params = {**location_params, **querie_params}

    return params

def modify_output_file_name(params):
    adder = ""
    for key in sorted(params.keys()):
        if params[key] != None and key != "_page":
            adder = adder + "_" + str(params[key])
    global args
    args.outputfilename = args.outputfilename + adder


def extract_path_from_url(urlstr):
    return "https://www.usnews.com/best-graduate-schools/api/search"

def get_temp_file_name(page):
    return temp_folder + "/" + str(page).zfill(3) + ".txt"

def create_initial_request_params(urlstr, page_num=1):
    url = extract_path_from_url(urlstr)
    params = extract_parameters_from_url(urlstr)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    return url, params, headers

def cleanup(delete_output=False):
    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)
    if delete_output and os.path.isfile(args.outputfilename):
        os.remove(args.outputfilename)

def print_error(response):
    status_code = response.status_code
    url = response.url
    print("An error occured while processing the url :\n" + url)
    print("Status Code : " + str(status_code) + "\n\n")
    
    response.raise_for_status()

def init_max_page(start_page, url, params, headers):
    params["_page"] = str(start_page)
    r = requests.get(url=url, params=params, headers=headers)
    response_json = r.json()
    time.sleep(1)
    return int(response_json["data"]["totalPages"])

def scrape_and_save_data(req_params, start_page=1, end_page=1):
    url, params, headers = req_params
    pause_time = max(args.pausetime, 1)

    start_page = int(start_page)
    end_page = int(end_page)
    
    cleanup(True)
    os.mkdir(temp_folder)
    
    max_page = init_max_page(start_page, url, params, headers)
    end_page = min(max(1, end_page), max_page)
    start_page = max(1, start_page)

    print("\nCollecting data from U.S.News...")

    for page in tqdm(range(start_page, end_page+1)):
        params["_page"] = str(page)
     
        if page > max_page:
            break

        r = requests.get(url=url, params=params, headers=headers)
        
        if r.status_code != requests.codes.ok:
            print_error(r)
            return
        
        #print(r.url)
        #print(get_file_name(page))
        
        f = open(get_temp_file_name(page), "w+")
        response_json = r.json()
        json.dump(response_json, f)
        f.close()
        
        time.sleep(pause_time)

    modify_output_file_name(params)

def init_headers():
    global output_headers
    output_headers = ["Rank", "Graduate School Name", "State", "City", "Score", "US News URL"]

def append_to_data_tablib(school_datas):
    global data_tablib
    header_existed = True

    if len(output_headers) == 0:
        header_existed = False
        init_headers()
        data_tablib = tablib.Dataset()

    for school_data in school_datas:
        g = tuple(GradSchool.getFromJSON(school_data))
        if header_existed == False:
            headers_tuple = tuple(output_headers)
            data_tablib.append(g)
            data_tablib = tablib.Dataset(*data_tablib, headers=headers_tuple)
            header_existed = True
        else:
            data_tablib.append(g)

def print_to_outputfile():
    filename = args.outputfilename + ".xls"
    with open(filename, "wb+") as f:
        f.write(data_tablib.export("xls"))
        f.close()

def parse_json_from_file():
    #print("Generating Output file...")
    page = int(args.startpage)
    while True:
        filename = get_temp_file_name(page)
        if os.path.isfile(filename) == False:
            break
        f = open(filename, "r")
        
        data = json.load(f)
        school_datas = data["data"]["items"]
        append_to_data_tablib(school_datas)

        f.close()
        page += 1
        

def main():
    global args
    
    args = parseargs()
    req_params = create_initial_request_params(args.url)
    scrape_and_save_data(req_params, args.startpage, args.endpage)
    parse_json_from_file()
    print_to_outputfile()
    cleanup()
main()