# U.S.News-Scrapper

U.S.News Scrapper is a Python library that collect data from the website of [usnews](https://www.usnews.com/best-graduate-schools) and output those data in a file for offline usage. Till now, it is only capable of collecting graduate schools data and output it in `.xls` format. After generating the `.xls` file, it will be opened by default excel file opener.

## Setup
Make sure that [Python 3](https://www.python.org/downloads) is already installed in your system.
### Using pip
```bash
$ pip install usnews_scrapper
```
alternatively you can install by [Using source](#using-source)

### Using source
First clone the repository. Then go to the repository and install the required packages using [pip](https://pip.pypa.io/en/stable/)
```bash
$ git clone https://github.com/OvroAbir/USNews-Scrapper.git
$ cd USNews-Scrapper
$ pip install -r requirements.txt
```

## Usage

### Command line usage
```
usnews_scrapper.py [-h] -u URL [-o OUTPUTFILENAME] [-p PAUSETIME] [--from STARTPAGE] [--to ENDPAGE]
```
Collects data from usnews and generates excel file.

Necessary Arguments:
```
-u URL, --url URL     		        The usnews address to collect data from. 
                                        Put the URL within qoutes i.e. " or ' .
```
Optional Arguments:
```
-h, --help            		        Show this help message and exit
-o OUTPUTFILENAME     		        The output file name without extension.
-p PAUSETIME, --pause PAUSETIME         The pause time between loading pages from usnews.
--from STARTPAGE      		        The page number from which the scrapper starts working.
--to ENDPAGE          		        The page number to which the scrapper works.
```

### Module usage
`usnews_scrapper.scrapper()` takes input the `url` as string. The other arguments are optional. This function will return absolute path to the output file.
```python
from usnews_scrapper import unsc
unsc(url:str, output_file_name:str, pause_time:int, from_page:int, to_page:int) -> str
```
See [Module example](#module-example) for examples.

## Examples

### Command line example
Copy the address of the page from usnews website and in the Command Prompt and enter this command -

```bash
$ cd USNews-Scrapper/usnews_scrapper/
$ python usnews_scrapper.py --url="https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings" -o file_name -p 2 --from=2 --to=5 
```
The output file will be saved in current directory under the name of `file_name_*.xls`. 

### Module example

```python
>>> from usnews_scrapper import unsc
>>> url = "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings"
>>> output_file = unsc(url=url, output_file_name="output", pause_time=2, from_page=2, to_page=5)
```
The output_file will contain the absolute path to the output file.

## Author

* **Joy Ghosh** - [www.ijoyghosh.com](https://www.ijoyghosh.com)
