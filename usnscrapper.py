import requests
import urllib.request
import time
import json
import queue
from argparse import ArgumentParser
from urllib import parse
import os
import shutil
import tablib
import sys
from tqdm import tqdm


#Global Variables
args = None
temp_folder = "./temp"
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

    url_help = "The usnews address to collect data from. Put the URL within qoutes i.e. \" or \' ."
    output_help = "The output file name without extension."
    pause_help = "The pause time between loading pages from usnews. Minimum pause time is 1 sec."
    from_help = "The page number from which the scrapper starts working."
    to_help = "The page number to which the scrapper works."

    parser.add_argument("-u", "--url", help=url_help, dest="url", default=defaulturl, type=str, required=True)
    parser.add_argument("-o", help=output_help, dest="outputfilename", default=default_output_file_name)
    parser.add_argument("-p", "--pause", help=pause_help, dest="pausetime", default=default_pause_time, type=int)
    parser.add_argument("--from", help=from_help, dest="startpage", default=default_start_page, type=int)
    parser.add_argument("--to", help=to_help, dest="endpage", default=default_end_page, type=int)

def get_parser_for_parsing():
    parser = ArgumentParser(description="Collects data from usnews and generates excel file")
    modifyparser(parser)

    return parser

def parseargs_from_cmd():
    parser = get_parser_for_parsing()
    args = parser.parse_args()

    return args

def parseargs_from_function_call(arguments):
    parser = get_parser_for_parsing()
    args = parser.parse_args(arguments)

    return args

def extract_parameters_from_url(url):
    location_params = {}
    parse_results = parse.urlsplit(url)

    output_sheet_name = "Ranking"
    
    locations = parse_results.path.split("/")[2:]
    program = locations[0]
    if program != "search":
        location_params["program"] = program
        output_sheet_name = program
    
    try:
        specialty = locations[1][:locations[1].rfind("-")]
        location_params["specialty"] = specialty
        output_sheet_name = specialty
    except:
        pass
    
    location_params["_page"] = "dummy"

    global args
    args["output_sheet_name"] = output_sheet_name.replace("-", " ").title()

    querie_params = dict(parse.parse_qsl(parse_results.query))    
    params = {**location_params, **querie_params}

    return params


def modify_output_file_name(params):
    global args
    adder = ""

    for key in sorted(params.keys()):
        if params[key] != None and key != "_page":
            adder = adder + "_" + str(params[key])
    adder = adder + "_" + str(args["year"])
    
    args["outputfilename"] = args["outputfilename"] + adder


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
    if delete_output and os.path.isfile(args["outputfilename"]):
        os.remove(args["outputfilename"])

def print_request_error(response):
    status_code = response.status_code
    url = response.url
    print("An error occured while processing the url :\n" + url)
    print("Status Code : " + str(status_code) + "\n\n")
    
    #response.raise_for_status()

def get_initial_infos(url, params, headers):
    params["_page"] = "1"
    r = requests.get(url=url, params=params, headers=headers)

    if r.status_code != requests.codes.ok:
        print_request_error(r)
        return

    response_json = r.json()
    time.sleep(1)
    max_page = int(response_json["data"]["totalPages"])
    year = response_json["data"]["hero"]["year"]

    return max_page, year


def decide_start_and_end_page(max_page, start_page, end_page):
    end_page = min(max(1, end_page), max_page)
    start_page = max(1, start_page)

    if start_page > end_page:
        start_page = end_page = min(start_page, end_page)

    return (start_page, end_page)


def scrape_and_save_data(req_params):
    url, params, headers = req_params
    
    cleanup(True)
    os.mkdir(temp_folder)
    
    print("\nCollecting data from U.S.News...")
    sys.stdout.flush()

    for page in tqdm(range(args["startpage"], args["endpage"]+1)):
        params["_page"] = str(page)

        r = requests.get(url=url, params=params, headers=headers)

        if r.status_code != requests.codes.ok:
            print_request_error(r)
            return
        
        f = open(get_temp_file_name(page), "w+")
        response_json = r.json()
        json.dump(response_json, f)
        f.close()
        
        time.sleep(args["pausetime"])

    modify_output_file_name(params)

def get_column_headers():
    output_headers = ["Rank", "Graduate School Name", "State", "City", "Score", "US News URL"]
    return tuple(output_headers)

def append_to_data_tablib(school_datas):
    global data_tablib

    if data_tablib == None:
        headers = get_column_headers()
        data_tablib = tablib.Dataset(title=args["output_sheet_name"])
        data_tablib.headers = headers

    for school_data in school_datas:
        g = tuple(GradSchool.getFromJSON(school_data))
        data_tablib.append(g)

def print_to_outputfile():
    if data_tablib == None:
        print("Data Tablib is None. Some error happened")
        sys.exit()

    filename = args["outputfilename"] = args["outputfilename"] + ".xls"
    with open(filename, "wb+") as f:
        f.write(data_tablib.export("xls"))
        f.close()

def parse_json_from_file():
    #print("Generating Output file...")
    locked_q = queue.Queue()

    for filename in sorted(os.listdir(temp_folder)):
        filename = temp_folder + "/" + filename
        if os.path.isfile(filename) == False:
            continue
        f = open(filename, "r")
        
        data = json.load(f)
        
        school_datas = data["data"]["items"]
        append_to_data_tablib(school_datas)

        if "itemsLocked" in data["data"] and data["data"].get("itemsLocked") != None:
            locked_q.put(data["data"]["itemsLocked"])

        f.close()
        
    while locked_q.empty() == False:
        append_to_data_tablib(locked_q.get())

def convert_and_check_args(req_params):
    global args
    args["startpage"] = int(args["startpage"])
    args["endpage"] = int(args["endpage"])
    args["pausetime"] = int(args["pausetime"])
    
    args["pausetime"] = min(max(args["pausetime"], 1), 10)
    args["startpage"] = max(1, args["startpage"])
    args["endpage"] = max(args["startpage"], args["endpage"])

    url, params, headers = req_params
    max_page, args["year"] = get_initial_infos(url, params, headers)
    args["startpage"], args["endpage"] = decide_start_and_end_page(max_page, args["startpage"], args["endpage"])

    if args["outputfilename"].endswith("xls"):
        args["outputfilename"] = args["outputfilename"][:-3]
    
    #if (args.url[0] not in ["\'", "\""]) or (args.url[:1] not in ["\'", "\""]):
    #    print("The URL must start and end with \" or \'")
    #    sys.exit()

    if "www.usnews.com/best-graduate-schools" not in args["url"]:
        print("Sorry. Only Graduate School rankings from usnews are supported for now.")
        sys.exit()
    
    msg = "Collecting data from \"{}\" \nFrom page {} to page {} with pause time of {} sec."
    print(msg.format(args["url"], args["startpage"], args["endpage"], args["pausetime"]))

    
def open_output_file():
    filename = args["outputfilename"]
    os.startfile(filename)


def run_scrapping_and_saving():
    req_params = create_initial_request_params(args["url"])
    convert_and_check_args(req_params)

    scrape_and_save_data(req_params)

    parse_json_from_file()
    print_to_outputfile()

    cleanup()
    open_output_file()

def create_argument_from_values(url, output_file_name, pause_time, from_page, to_page):
    arguments = []
    arguments.append("--url")
    arguments.append(url)

    if output_file_name is not None:
        arguments.append("-o")
        arguments.append(str(output_file_name))

    if pause_time is not None:
        arguments.append("--pause")
        arguments.append(str(pause_time))

    if from_page is not None:
        arguments.append("--from")
        arguments.append(str(from_page))

    if to_page is not None:
        arguments.append("--to")
        arguments.append(str(to_page))
    
    return arguments

def usnews_scrapper(url, output_file_name=None, pause_time=None, from_page=None, to_page=None):
    arguments = create_argument_from_values(url, output_file_name, pause_time, from_page, to_page)
    
    global args
    args = vars(parseargs_from_function_call(arguments))
    run_scrapping_and_saving()

def main():
    global args
    args = vars(parseargs_from_cmd())
    run_scrapping_and_saving()


if __name__ == "__main__":
    main()
