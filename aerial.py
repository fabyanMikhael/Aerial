from time import time
import requests, sys, time
import json, logging, os
from zipfile import ZipFile

def rem_suffix(self, txt):
    if self.endswith(txt):
        self = self[:-(len(txt))]
    return self


def upload(object_name : str, response):
    object_name = object_name
    with open(object_name, 'rb') as f:
        files = {'file': (object_name, f)}
        http_response = requests.post(response['url'], data=response['fields'], files=files)


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

    version = input("version: ")
    if version == "" or version == None:
        Error()

    dependencies = []
    print("Dependencies (enter to stop listing): ")
    while True:
        dep = input("->")
        if dep == None or dep == "":
            break
        dependencies.append(dep)


    time_ = time.time()
    TXT = requests.get(f"{BASE_URL}{UPLOAD}", data=json.dumps({'file' : filename, 'info':{"version" : version, "dependencies" : dependencies}})).text 
    CheckForError(TXT, file_to_remove = filename)
    REQ = json.loads(TXT)
    try:
        upload(filename,REQ)
        print(f"\nSuccessfully uploaded {rem_suffix(filename,'.zip')} package ({GetHumanReadable(os.path.getsize(filename))}).\n took {time.time() - time_:.2f} seconds!")
    except:
        print(f"\nError: file {rem_suffix(filename,'.zip')} ({GetHumanReadable(File_size)}) was unable to be uploaded. (file size might be too large)")
    os.remove(filename)

if instruction.lower() == "install":
    time_ = time.time()
    TXT = requests.get(f"{BASE_URL}{DOWNLOAD}", data=filename).text 
    CheckForError(TXT)
    r = requests.get(str(TXT), allow_redirects=True)
    filename += ".zip"
    open(filename, 'wb').write(r.content)
    with ZipFile(filename, 'r') as zip:
        zip.extractall(path='packages/'+rem_suffix(filename,".zip"))
    File_size = GetHumanReadable(os.path.getsize(filename))
    os.remove(filename)
    print(f"\nSuccessfully installed {rem_suffix(filename,'.zip')} package ({File_size}). \ntook {time.time() - time_:.2f} seconds!")

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
    print(f"~~~~~~~Packages (total: {len(packages)})~~~~~~~")
    for key in packages:
        print(f"{key}: {packages[key]}")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
