
from socket import timeout
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
import json, time
from aws_storage import Bucket



IPS : dict[str,timeout] = {}

AerialBucket = Bucket(bucket_name= 'aerialbucket',directory='repos/')


TIMEOUT_SECONDS = 60
CALLS_LIMIT = 6

MIN_FILE_SIZE = 0
MAX_FILE_SIZE = 1048578

class Timeout():
  def __init__(self) -> None:
      self.requests : int = 1
      self.time : int = time.time()

def CheckIp(ip : str, WSH):
  Timeout_obj : Timeout = None
  if ip in IPS:
      Timeout_obj = IPS[ip]
  else :
      Timeout_obj = Timeout()
      IPS[ip] = Timeout_obj
    
  Timeout_obj.requests += 1


  if (tmp := time.time()) - Timeout_obj.time >= TIMEOUT_SECONDS:
    Timeout_obj.requests = 1
    Timeout_obj.time = tmp

  if Timeout_obj.requests >= CALLS_LIMIT:
    WSH.write(f"Error: Timeout! wait {TIMEOUT_SECONDS - time.time() + Timeout_obj.time:.2f} seconds")
    return False

  return True


class UploadPermission(WebSocketHandler):
  def get(self):
    tmp = ( json.loads( self.request.body ) )
    object_name = tmp['file']
    info = tmp['info']
    ip = self.request.remote_ip
    if not CheckIp(ip,self): return
    if object_name.endswith('.zip'):
      if (AerialBucket.Exists(object_name.removesuffix(".zip") + "/" + object_name)):
        self.write("Error: Package name already exists!")
        return
      AerialBucket.CreateFolder(directory_ := object_name.removesuffix(".zip"))
      AerialBucket.upload(object_name= directory_  + "/info.json",
                          return_url=False,
                          file=json.dumps({
                            "name": directory_,
                            "version": info['version'],
                            "dependencies": info['dependencies']
                                          }))

      POST = AerialBucket.GetUploadPost(object_name=directory_ + "/" + object_name,
                                        expiration=20,
                                        conditions=[{"bucket": "aerialbucket"},
                                                    ["starts-with", "$key",  "repos/"],
                                                    ["content-length-range", MIN_FILE_SIZE, MAX_FILE_SIZE]
                                                    ])
      self.write(POST)
      return

    self.write("Error: Cannot upload non-zip files!")
    
class PackageInfo(WebSocketHandler):
  def get(self):
    object_name = str(self.request.body).removeprefix('b').replace("'", '') + ".zip"
    ip = self.request.remote_ip
    if not CheckIp(ip,self): return
    if not AerialBucket.Exists(object_name.removesuffix(".zip")+"/"+object_name):
      self.write("Error: failed to find package.")
      return

    info = AerialBucket.Download(object_name.removesuffix(".zip")+"/info.json")
    self.write(info)

class DownloadPermission(WebSocketHandler):
  def get(self):
    object_name = str(self.request.body).removeprefix('b').replace("'", '') + ".zip"
    ip = self.request.remote_ip
    if not CheckIp(ip,self): return
    if not AerialBucket.Exists(object_name.removesuffix(".zip")+"/"+object_name):
      self.write("Error: failed to find package.")
      return
    post_req = AerialBucket.getLink(object_name.removesuffix(".zip")+"/" +object_name, expiration=10)
    self.write(post_req)

class CheckMaxFileSize(WebSocketHandler):
  def get(self):
    self.write(str(MAX_FILE_SIZE))

class AllPackages(WebSocketHandler):
  def get(self):
    ip = self.request.remote_ip
    if not CheckIp(ip,self): return
    self.write( json.dumps(AerialBucket.GetAllObjects()) )

def make_app():
  urls = [
    ("/api/UploadPermission", UploadPermission),
    ("/api/DownloadPermission", DownloadPermission),
    ("/api/CheckMaxFileSize", CheckMaxFileSize),
    ("/api/PackageInfo", PackageInfo),
    ("/api/AllPackages", AllPackages)
         ]
  return Application(urls, debug=False)

def start(a=None,b=None):
  app = make_app()
  app.listen(3000)
  IOLoop.instance().start()

if __name__ == '__main__':
  start()