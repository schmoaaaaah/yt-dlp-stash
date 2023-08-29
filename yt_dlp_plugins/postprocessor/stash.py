# ⚠ Don't use relative imports
import json

from yt_dlp.postprocessor.common import PostProcessor
import stashapi.log as log
from stashapi.stashapp import StashInterface
from time import sleep

# ℹ️ See the docstring of yt_dlp.postprocessor.common.PostProcessor

# ⚠ The class name must end in "PP"


class StashPP(PostProcessor):
    def __init__(self, downloader=None, stashurl: str='http:localhost:9999', **kwargs):
        # ⚠ Only kwargs can be passed from the CLI, and all argument values will be string
        # Also, "downloader", "when" and "key" are reserved names
        super().__init__(downloader)
        self.tag = None
        self._kwargs = kwargs
        self.stash = StashInterface(
            {
                "scheme": stashurl.split(':')[0],
                "domain": stashurl.split(':')[1],
                "port": stashurl.split(':')[2],
                "logger": log
            }
        )

    # ℹ️ See docstring of yt_dlp.postprocessor.common.PostProcessor.run
    def run(self, info):
        stash_meta_job = self.stash.metadata_scan(info['requested_downloads'][0]['__finaldir'])
        self.to_screen("Scanning metadata on path: " + info['requested_downloads'][0]['__finaldir'])
        gql_query = """
        query FindJob($jobid:ID!){
        	findJob(input:{id:$jobid}){
        		status,
        		progress,
        		id
        	}
        }
        """
        gql_variables = {"jobid": int(stash_meta_job)}
        while self.stash.call_gql(gql_query, gql_variables)["findJob"]["status"] != "FINISHED":
            sleep(0.5)
        scene = self.stash.find_scenes({"path": {"modifier": "EQUALS", "value": info['requested_downloads'][0]['filepath']}})
        self.to_screen("Found scene with id: " + scene[0]["id"])
        self.tag = self.stash.find_tags({"name": {"modifier": "EQUALS", "value": "scrape"}})
        if len(self.tag) == 0:
            self.tag[0] = self.stash.create_tag({"name": "scrape"})
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