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
        stash_meta_job = self.stash.metadata_scan()
        query = """
        query FindJob($jobid:ID!){
        	findJob(input:{id:$jobid}){
        		status,
        		progress,
        		id
        	}
        }
        """
        variables = {"jobid": stash_meta_job["metadataScan"]}
        stash_job = self.stash.call_gql(query, variables)
        while self.stash.call_gql(query, variables)["findJob"]["status"] != "FINISHED":
            sleep(1)
        scene = self.stash.find_scenes({"path": {"modifier": "INCLUDES", "value": info["filepath"]}})
        self.tag = self.stash.find_tags({"name": {"modifier": "EQUALS", "value": "scrape"}})
        if len(self.tag) == 0:
            self.tag[0] = self.stash.create_tag({"name": "scrape"})
        update_scene = {
            "id": scene[0]["id"],
            "title": info["title"],
            "details": info["description"],
            "url": info["webpage_url"],
            "date": info["upload_date"],
            "tag_ids": [self.tag[0]["id"]],
            "cover_image": info["thumbnail"],
        }
        self.stash.update_scene(update_scene)
        return [], info