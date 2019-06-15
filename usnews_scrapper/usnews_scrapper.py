"""USNews-Scrapper

This script is built to collect informations about Grad Schools from 
https://www.usnews.com/best-graduate-schools. 

This script takes the url as input and generates output as (.xls) file.

This file can also be imported as a module and contains the following
functions:

    * usnews_scrapper - returns the path of the output file
    * _main - the main function of the script
"""

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



class GradSchool:
    def __init__(self, name, state, city, rank, is_tied, score, school_url):
        self.__name = name
        self.__state = state
        self.__city = city
        
        try:
            self.__rank = int(rank)
        except (ValueError, TypeError) as e:
            self.__rank = rank

        self.__is_tied = is_tied
        
        try:
            self.__score = float(score)
        except (ValueError, TypeError) as e:
            self.__score = score

        self.__school_url = school_url

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
        yield self.__rank
        yield self.__name
        yield self.__state
        yield self.__city
        #yield self.__is_tied
        yield self.__score
        yield self.__school_url

    def __str__(self):
        return "name : {} \nstate : {} \ncity : {} \nrank : {} \nis tied : {} \nscore : {} \nschool url : {}".format(self.__name, self.__state, self.__city, self.__rank, self.__is_tied, self.__score, self.__school_url)


class USNewsScrapper:
    def __init__(self):    
        self.__args = None
        self.__temp_folder = "./temp"
        self.__data_tablib = None
        self.__called_as_module = False

    def __modifyparser(self, parser):
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

    def __get_parser_for_parsing(self):
        parser = ArgumentParser(description="Collects data from usnews and generates excel file")
        self.__modifyparser(parser)

        return parser

    def __parseargs_from_cmd(self):
        parser = self.__get_parser_for_parsing()
        args = parser.parse_args()

        return args

    def __parseargs_from_function_call(self, arguments):
        parser = self.__get_parser_for_parsing()
        args = parser.parse_args(arguments)

        return args

    def __extract_parameters_from_url(self, url):
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

        #global self.__args
        self.__args["output_sheet_name"] = output_sheet_name.replace("-", " ").title()

        querie_params = dict(parse.parse_qsl(parse_results.query))    
        params = {**location_params, **querie_params}

        return params


    def __modify_output_file_name(self, params):
        #global __args
        adder = ""

        for key in sorted(params.keys()):
            if params[key] != None and key != "_page":
                adder = adder + "_" + str(params[key])
        adder = adder + "_" + str(self.__args["year"])
        
        self.__args["outputfilename"] = self.__args["outputfilename"] + adder


    def __extract_path_from_url(self, urlstr):
        return "https://www.usnews.com/best-graduate-schools/api/search"

    def __get_temp_file_name(self, page):
        return self.__temp_folder + "/" + str(page).zfill(3) + ".txt"

    def __create_initial_request_params(self, urlstr, page_num=1):
        url = self.__extract_path_from_url(urlstr)
        params = self.__extract_parameters_from_url(urlstr)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        return url, params, headers

    def __cleanup(self, delete_output=False):
        if os.path.isdir(self.__temp_folder):
            shutil.rmtree(self.__temp_folder)
        if delete_output and os.path.isfile(self.__args["outputfilename"]):
            os.remove(self.__args["outputfilename"])

    def __print_request_error(self, response):
        status_code = response.status_code
        url = response.url
        
        if self.__called_as_module == False:
            print("An error occured while processing the url :\n" + url)
            print("Status Code : " + str(status_code) + "\n\n")
        else:
            response.raise_for_status()

    def __get_initial_infos(self, url, params, headers):
        params["_page"] = "1"
        r = requests.get(url=url, params=params, headers=headers)

        if r.status_code != requests.codes.ok:
            __print_request_error(r)
            return

        response_json = r.json()
        time.sleep(1)
        max_page = int(response_json["data"]["totalPages"])
        year = response_json["data"]["hero"]["year"]

        return max_page, year


    def __decide_start_and_end_page(self, max_page, start_page, end_page):
        end_page = min(max(1, end_page), max_page)
        start_page = max(1, start_page)

        if start_page > end_page:
            start_page = end_page = min(start_page, end_page)

        return (start_page, end_page)


    def __scrape_and_save_data(self, req_params):
        url, params, headers = req_params
        
        self.__cleanup(True)
        os.mkdir(self.__temp_folder)
        
        if self.__called_as_module == False:
            print("\nCollecting data from U.S.News...")
        sys.stdout.flush()

        for page in tqdm(range(self.__args["startpage"], self.__args["endpage"]+1), disable=self.__called_as_module):
            params["_page"] = str(page)

            r = requests.get(url=url, params=params, headers=headers)

            if r.status_code != requests.codes.ok:
                self.__print_request_error(r)
                return
            
            f = open(self.__get_temp_file_name(page), "w+")
            response_json = r.json()
            json.dump(response_json, f)
            f.close()
            
            time.sleep(self.__args["pausetime"])

        self.__modify_output_file_name(params)

    def __get_column_headers(self):
        output_headers = ["Rank", "Graduate School Name", "State", "City", "Score", "US News URL"]
        return tuple(output_headers)

    def __append_to_data_tablib(self, school_datas):
        if self.__data_tablib == None:
            headers = self.__get_column_headers()
            self.__data_tablib = tablib.Dataset(title=self.__args["output_sheet_name"])
            self.__data_tablib.headers = headers

        for school_data in school_datas:
            g = tuple(GradSchool.getFromJSON(school_data))
            self.__data_tablib.append(g)

    def __print_to_outputfile(self):
        if self.__data_tablib == None:
            print("Data Tablib is None. Some error happened")
            sys.exit()

        filename = self.__args["outputfilename"] = self.__args["outputfilename"] + ".xls"
        with open(filename, "wb+") as f:
            f.write(self.__data_tablib.export("xls"))
            f.close()

    def __parse_json_from_file(self):
        #print("Generating Output file...")
        locked_q = queue.Queue()

        for filename in sorted(os.listdir(self.__temp_folder)):
            filename = os.path.join(self.__temp_folder, filename)
            #filename = self.__temp_folder + "/" + filename
            if os.path.isfile(filename) == False:
                continue
            f = open(filename, "r")
            
            data = json.load(f)
            
            school_datas = data["data"]["items"]
            self.__append_to_data_tablib(school_datas)

            if "itemsLocked" in data["data"] and data["data"].get("itemsLocked") != None:
                locked_q.put(data["data"]["itemsLocked"])

            f.close()
            
        while locked_q.empty() == False:
            self.__append_to_data_tablib(locked_q.get())

    def __convert_and_check_args(self, req_params):
        #global __args
        self.__args["startpage"] = int(self.__args["startpage"])
        self.__args["endpage"] = int(self.__args["endpage"])
        self.__args["pausetime"] = int(self.__args["pausetime"])
        
        self.__args["pausetime"] = min(max(self.__args["pausetime"], 1), 10)
        self.__args["startpage"] = max(1, self.__args["startpage"])
        self.__args["endpage"] = max(self.__args["startpage"], self.__args["endpage"])

        url, params, headers = req_params
        max_page, self.__args["year"] = self.__get_initial_infos(url, params, headers)
        self.__args["startpage"], self.__args["endpage"] = self.__decide_start_and_end_page(max_page, self.__args["startpage"], self.__args["endpage"])

        if self.__args["outputfilename"].endswith("xls"):
            self.__args["outputfilename"] = self.__args["outputfilename"][:-3]
        
        #if (args.url[0] not in ["\'", "\""]) or (args.url[:1] not in ["\'", "\""]):
        #    print("The URL must start and end with \" or \'")
        #    sys.exit()

        if "usnews.com/best-graduate-schools" not in self.__args["url"]:
            print("Sorry. Only Graduate School rankings from usnews are supported for now.")
            sys.exit()
        
        msg = "Collecting data from \"{}\" \nFrom page {} to page {} with pause time of {} sec."
        if self.__called_as_module == False:
            print(msg.format(self.__args["url"], self.__args["startpage"], self.__args["endpage"], self.__args["pausetime"]))

        
    def __open_output_file(self):
        filename = self.__args["outputfilename"]
        os.startfile(filename)


    def __run_scrapping_and_saving(self):
        req_params = self.__create_initial_request_params(self.__args["url"])
        self.__convert_and_check_args(req_params)

        self.__scrape_and_save_data(req_params)

        self.__parse_json_from_file()
        self.__print_to_outputfile()

        self.__cleanup()
        if self.__called_as_module == False:
            self.__open_output_file()

    def __create_argument_from_values(self, url, output_file_name, pause_time, from_page, to_page):
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

    def __get_outfile_name_with_working_dir(self):
        return os.path.join(os.getcwd(), self.__args["outputfilename"])

    def usnews_scrapper_for_cmd(self):
        self.__args = vars(self.__parseargs_from_cmd())
        self.__run_scrapping_and_saving()

    def usnews_scrapper_for_function_call(self, url, output_file_name, pause_time, from_page, to_page):    
        arguments = self.__create_argument_from_values(url, output_file_name, pause_time, from_page, to_page)
        self.__called_as_module = True
        
        self.__args = vars(self.__parseargs_from_function_call(arguments))
        self.__run_scrapping_and_saving() 
        
        return self.__get_outfile_name_with_working_dir()


def usnews_scrapper(url:str, output_file_name:str=None, pause_time:int=None, from_page:int=None, to_page:int=None) -> str:
    """ Collects data from usnews website and outputs a (.xls) file.

    Parameters
    ----------
    url : str
        URL of the usnews page from which to collect data.
    output_file_name : str, optional
        The expected name of the output file name. The output
        file name will start with this string.
    pause_time : int, optional
        The time between two successive request calls.
    from_page : int, optional
        The page number from which function will start to collect data.
    to_page : int, optional
        The page number upto which function will collect data.

    Returns
    -------
    str
        The absolute path to the output file.
    """
    
    usnews_scrapper_obj = USNewsScrapper()
    return usnews_scrapper_obj.usnews_scrapper_for_function_call(url, output_file_name, pause_time, from_page, to_page)
    

def _main():
    usnews_scrapper_obj = USNewsScrapper()
    usnews_scrapper_obj.usnews_scrapper_for_cmd()

if __name__ == "__main__":
    _main()
