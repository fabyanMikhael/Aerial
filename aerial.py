from time import time
import requests, sys, time
import json, logging, os
from zipfile import ZipFile

os.system("color")
COLOR_GREEN = "\u001b[32m"
COLOR_CYAN = "\u001b[36m"
COLOR_END = "\x1b[0m"
COLOR_RED_PINK = "\u001b[38;5;197m" 

def rem_suffix(self, txt):
    if self.endswith(txt):
        self = self[:-(len(txt))]
    return self


def upload(object_name : str, response):
    object_name = object_name
    with open(object_name, 'rb') as f:
        files = {'file': (object_name, f)}
        http_response = requests.post(response['url'], data=response['fields'], files=files)

def DownloadFile(file_name, link):
    with open(file_name, "wb") as f:
        print(f"Downloading {COLOR_RED_PINK}{rem_suffix(file_name, '.zip')}{COLOR_END} package")
        response = requests.get(link, allow_redirects=True, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                cl_s = ""
                cl_e = ""
                if done == 50:
                    cl_s = "\u001b[32m"
                    cl_e = "\x1b[0m"
                sys.stdout.write(("\r[%s\x1b[0m%s]" % ('\u001b[32m=' * done, ' ' * (50-done))) + f" {cl_s}{dl * 100 / total_length : .2f} % {cl_e} " )    
                sys.stdout.flush()

def GetHumanReadable(size,precision=2):
    suffixes=['B','Kb','Mb','Gb','Tb']
    suffixIndex = 0
    while size > 1024 and suffixIndex < 4:
        suffixIndex += 1 
        size = size/1024.0
    return "%.*f%s"%(precision,size,suffixes[suffixIndex])

def get_all_file_paths(directory) -> list:

    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            if "aerial.py" in filename:
                continue
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths        

def Zip_Everything(zip_name: str = "my_python_files", directory: str = '.') -> str:
        files = get_all_file_paths(directory)
        zip_name += ".zip"
        for tmp in files:
            if zip_name.lower() in tmp.lower():
                logging.error("do NOT attempt to upload with a package name that is already taken up by a .zip file. (otherwise it will eat up your entire drive in a few minutes)")
                exit()
        with ZipFile(zip_name,'w') as zip:
            for file in files:
                zip.write(file)
            return zip_name




sys.argv.pop(0)

def Error():
    print("Error: use 'aerial.py <install/upload> <package name.>'")
    exit()    

def CheckForError(TXT, file_to_remove = None):
    if (error_msg := str(TXT)).lower().startswith("error"):
        print(error_msg) 
        if file_to_remove != None: os.remove(file_to_remove)
        exit()

if len(sys.argv) < 1 or len(sys.argv) > 2:
    Error()

if sys.argv[0].lower() not in ['install', 'upload', 'info', 'all']:
    Error()


instruction = sys.argv[0]
filename = sys.argv[1] if len(sys.argv) == 2 else ''

# CHANGE IP TO SERVER IP
BASE_URL = "http://localhost:3000/api/"
UPLOAD = "UploadPermission"
DOWNLOAD = "DownloadPermission"
CHECKFILESIZE = "CheckMaxFileSize"
PACKAGEINFO = "PackageInfo"
ALLPACKAGES = "AllPackages"

if instruction.lower() == "upload":
    Max_size = int(requests.get(f'{BASE_URL}{CHECKFILESIZE}').text)
    filename = Zip_Everything(zip_name=sys.argv[1])
    File_size = os.path.getsize(filename)
    if File_size >= Max_size:
        print(f"\nError: file {filename} ({GetHumanReadable(File_size)}) was unable to be uploaded due to file size limit. (Max file size: {GetHumanReadable(Max_size)})")
        os.remove(filename)
        exit()

    version = input(f"version: {COLOR_RED_PINK}")
    if version == "" or version == None:
        Error()

    dependencies = []
    print(f"{COLOR_GREEN}Dependencies {COLOR_CYAN}(enter to stop listing):{COLOR_CYAN} ")
    while True:
        dep = input(f"{COLOR_END}->{COLOR_RED_PINK}")
        if dep == None or dep == "":
            break
        dep = dep.strip()
        dependencies.append(dep)
    print(COLOR_END)

    time_ = time.time()
    TXT = requests.get(f"{BASE_URL}{UPLOAD}", data=json.dumps({'file' : filename, 'info':{"version" : version, "dependencies" : dependencies}})).text 
    CheckForError(TXT, file_to_remove = filename)
    REQ = json.loads(TXT)
    try:
        upload(filename,REQ)
        print(f"\nSuccessfully uploaded {COLOR_RED_PINK}{rem_suffix(filename,'.zip')}{COLOR_END} package {COLOR_CYAN}({GetHumanReadable(os.path.getsize(filename))}){COLOR_END}.\n took {COLOR_GREEN}{time.time() - time_:.2f}{COLOR_END} seconds!")
    except:
        print(f"\nError: file {rem_suffix(filename,'.zip')} {COLOR_CYAN}({GetHumanReadable(File_size)}){COLOR_END} was unable to be uploaded. (file size might be too large)")
    os.remove(filename)

if instruction.lower() == "install":
    time_ = time.time()
    TXT = requests.get(f"{BASE_URL}{DOWNLOAD}", data=filename).text 
    CheckForError(TXT)
    filename += ".zip"
    DownloadFile(filename, str(TXT))
    with ZipFile(filename, 'r') as zip:
        zip.extractall(path='packages/'+rem_suffix(filename,".zip"))
    File_size = GetHumanReadable(os.path.getsize(filename))
    os.remove(filename)
    print(f"\nSuccessfully installed {COLOR_RED_PINK}{rem_suffix(filename,'.zip')}{COLOR_END} package {COLOR_CYAN}({File_size}){COLOR_END}. \ntook {COLOR_GREEN}{time.time() - time_:.2f}{COLOR_END} seconds!")

if instruction.lower() == "info":
    TXT = requests.get(f"{BASE_URL}{PACKAGEINFO}", data=filename).text
    CheckForError(TXT)
    for key in (info := json.loads(TXT)):
        if key.lower() == "dependencies":
            print("dependencies")
            dependencies = info[key]
            for dependency in dependencies:
                print(f"\t- {dependency}")
        else:
            print(f"{key}: {info[key]}")

if instruction.lower() == "all":
    TXT = requests.get(f"{BASE_URL}{ALLPACKAGES}").text
    CheckForError(TXT)
    packages = json.loads(TXT)
    print(f"{COLOR_GREEN}~~~~~~~{COLOR_CYAN}Packages (total: {len(packages)}){COLOR_GREEN}~~~~~~~{COLOR_END}")
    for key in packages:
        print(f"{key}: {COLOR_RED_PINK}{packages[key]}{COLOR_END}")
    print(f"{COLOR_GREEN}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{COLOR_END}")
