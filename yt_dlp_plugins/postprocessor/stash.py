# ⚠ Don't use relative imports
from yt_dlp.postprocessor.common import PostProcessor
import stashapi.log as log
from stashapi.stashapp import StashInterface
from time import sleep
from pathlib import Path

# ℹ️ See the docstring of yt_dlp.postprocessor.common.PostProcessor

# ⚠ The class name must end in "PP"


class StashPP(PostProcessor):
    def __init__(self, downloader=None, scheme: str='http', host: str='localhost', port: int=9999, apikey: str='', sessioncookie: str='', searchpathoverride: str='', **kwargs):
        # ⚠ Only kwargs can be passed from the CLI, and all argument values will be string
        # Also, "downloader", "when" and "key" are reserved names
        super().__init__(downloader)
        self.tag = None
        self._kwargs = kwargs
        stash_args = {
                "Scheme": scheme,
                "Host": host,
                "Port": port,
                "Logger": log
            }
        if apikey:
            stash_args["ApiKey"] = apikey
        elif sessioncookie:
            stash_args["SessionCookie"] = sessioncookie
        self.stash = StashInterface(stash_args)
        self.searchpathoverride = searchpathoverride

    # ℹ️ See docstring of yt_dlp.postprocessor.common.PostProcessor.run
    def run(self, info):
        if self.searchpathoverride != '':
            filepath = (self.searchpathoverride + info['requested_downloads'][0]['filename'][1:]).replace("//","/")
            dirpath = "/".join(filepath.split("/")[0:-1])
        else:
            filepath = info['requested_downloads'][0]['filepath']
            dirpath = info['requested_downloads'][0]['__finaldir']
        self.to_screen("Scanning metadata on path: " + dirpath)
        try:
            stash_meta_job = self.stash.metadata_scan(paths=dirpath,flags={
                "scanGenerateCovers": False,
                "scanGeneratePreviews":False,
                "scanGenerateImagePreviews": False,
                "scanGenerateSprites": False,
                "scanGeneratePhashes":False,
                "scanGenerateThumbnails": False,
                "scanGenerateClipPreviews": False
            })
        except Exception as e:
            self.to_screen("Error on metadata scan: " + str(e))
            return [], info
        while self.stash.find_job(stash_meta_job)["status"] != "FINISHED":
            sleep(0.5)
        scene = self.stash.find_scenes({"path": {"modifier": "EQUALS", "value": filepath}})
        self.to_screen("Found scene with id: " + scene[0]["id"])
        self.tag = self.stash.find_tags({"name": {"modifier": "EQUALS", "value": "scrape"}})
        if len(self.tag) == 0:
            self.tag = [self.stash.create_tag({"name": "scrape"})]
        update_scene = {
            "id": scene[0]["id"],
            "title": info["title"],
            "url": info["webpage_url"],
            "tag_ids": [self.tag[0]["id"]],
            "cover_image": info["thumbnail"],
        }
        if "description" in info:
            update_scene["details"] = info["description"]
        if "upload_date" in info:
            update_scene["date"] = info["upload_date"][0:4] + "-" + info["upload_date"][4:6] + "-" + info["upload_date"][6:8]
        self.stash.update_scene(update_scene)
        self.to_screen("Updatet Scene")
        return [], info