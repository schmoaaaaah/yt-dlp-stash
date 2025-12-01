# ⚠ Don't use relative imports
from yt_dlp.postprocessor.common import PostProcessor
import stashapi.log as log
from stashapi.stashapp import StashInterface
from time import sleep
from pathlib import Path

# ℹ️ See the docstring of yt_dlp.postprocessor.common.PostProcessor

# ⚠ The class name must end in "PP"


class StashPP(PostProcessor):
    def __init__(
        self,
        downloader=None,
        scheme: str = "http",
        host: str = "localhost",
        port: int = 9999,
        apikey: str = "",
        sessioncookie: str = "",
        searchpathoverride: str = "",
        scrapemethod: str = "yt_dlp",
        **kwargs,
    ):
        # ⚠ Only kwargs can be passed from the CLI, and all argument values will be string
        # Also, "downloader", "when" and "key" are reserved names
        super().__init__(downloader)
        self.tag = None
        self._kwargs = kwargs
        self.scrapemethod = scrapemethod
        stash_args = {"Scheme": scheme, "Host": host, "Port": port, "Logger": log}
        if apikey:
            stash_args["ApiKey"] = apikey
        elif sessioncookie:
            stash_args["SessionCookie"] = sessioncookie
        self.stash = StashInterface(stash_args)
        self.searchpathoverride = searchpathoverride

    def run(self, info):
        if self.scrapemethod == "stash":
            # Updated logic uses Stash GraphQL API to update the scene
            return self.stash_scrape(info)
        return self.ytdlp_scrape(info)

    def ytdlp_scrape(self, info, scanpath: bool = True, scene=[]):
        scene = scene
        filepath, dirpath = self._get_paths(info)
        if len(scene) == 0:
            if scanpath:
                try:
                    self._scan_path(dirpath)
                except Exception as e:
                    self.write_debug(f"[Debug] Error during metadata scan: {e}")
                    return [], info

            # Step 5: Search for the scene by file path
            try:
                scene = self._search_scene_by_path(filepath)
            except Exception as e:
                self.to_screen(
                    "[Error] No scene found after metadata scan. Please verify the path and metadata settings."
                )
                self.write_debug(f"[Debug] Error during scene search: {e}")
                return [], info
        self.write_debug(f"Found scene with id: {scene[0]['id']}")
        self.tag = self.stash.find_tags(
            {"name": {"modifier": "EQUALS", "value": "scrape"}}
        )
        if len(self.tag) == 0:
            self.tag = [self.stash.create_tag({"name": "scrape"})]
        update_scene = {
            "id": scene[0]["id"],
            "url": info["webpage_url"],
            "tag_ids": [self.tag[0]["id"]],
        }
        if "title" in info:
            update_scene["title"] = info["title"]
        if "thumbnail" in info:
            update_scene["cover_image"] = info["thumbnail"]
        if "description" in info:
            update_scene["details"] = info["description"]
        if "upload_date" in info:
            update_scene["date"] = (
                info["upload_date"][0:4]
                + "-"
                + info["upload_date"][4:6]
                + "-"
                + info["upload_date"][6:8]
            )
        self.stash.update_scene(update_scene)
        self.to_screen(f"[Info] Updated Scene with id: {scene[0]['id']}")
        return [], info

    def stash_scrape(self, info):
        try:
            filepath, dirpath = self._get_paths(info)

            # Debugging: Print the file path and directory path
            self.write_debug(f"[Debug] Filepath for metadata scan: {filepath}")
            self.write_debug(f"[Debug] Directory for metadata scan: {dirpath}")

            # Step 3: Metadata scan for the input file
            try:
                self._scan_path(dirpath)
            except Exception as e:
                self.write_debug(f"[Debug] Error during metadata scan: {e}")
                return [], info

            # Step 5: Search for the scene by file path
            try:
                scene = self._search_scene_by_path(filepath)
            except Exception as e:
                self.to_screen(
                    "[Error] No scene found after metadata scan. Please verify the path and metadata settings."
                )
                self.write_debug(f"[Debug] Error during scene search: {e}")
                return [], info

            scene_id = scene[0]["id"]
            self.write_debug(f"[Debug] Found scene with id: {scene_id}")

            # Step 6: Scrape metadata from URL
            if "webpage_url" not in info:
                self.report_warning("[Warning] No URL found for scraping")
                return [], info

            self.write_debug(
                f"[Debug] Scraping metadata from URL: {info['webpage_url']}"
            )
            scene_data = self._scrape_scene_by_url(info["webpage_url"])

            if not scene_data:
                self.report_warning(
                    "[Warning] Error or no data found during scraping. Falling back to yt-dlp data."
                )
                self.ytdlp_scrape(info, scanpath=False, scene=scene)
                return [], info

            # Step 7: Update the scene data using the scraped information
            update_scene = {
                "id": scene_id,
                "url": info.get("webpage_url"),
            }

            if scene_data.get("title"):
                update_scene["title"] = scene_data["title"]
            elif info.get("title"):
                update_scene["title"] = info["title"]

            if scene_data.get("details"):
                update_scene["details"] = scene_data["details"]
            elif info.get("description"):
                update_scene["details"] = info["description"]

            if scene_data.get("date"):
                update_scene["date"] = scene_data["date"]
            elif info.get("upload_date"):
                update_scene["date"] = (
                    info["upload_date"][0:4]
                    + "-"
                    + info["upload_date"][4:6]
                    + "-"
                    + info["upload_date"][6:8]
                )

            if scene_data.get("image"):
                update_scene["cover_image"] = scene_data["image"]
            elif info.get("thumbnail"):
                update_scene["cover_image"] = info["thumbnail"]

            update_scene["tag_ids"] = []
            if scene_data.get("tags"):
                for tag in scene_data["tags"]:
                    tag_name = tag["name"]
                    existing_tag = self.stash.find_tags(
                        {"name": {"modifier": "EQUALS", "value": tag_name}}
                    )

                    if existing_tag and len(existing_tag) > 0:
                        self.write_debug(
                            f"[Debug] Found existing tag: {existing_tag[0]['name']} with ID: {existing_tag[0]['id']}"
                        )
                        update_scene["tag_ids"].append(existing_tag[0]["id"])
                    else:
                        # Create the tag if it doesn't exist
                        self.write_debug(f"[Debug] Creating new tag: {tag_name}")
                        new_tag = {"name": tag_name}
                        created_tag = self.stash.create_tag(new_tag)
                        update_scene["tag_ids"].append(created_tag["id"])

            # Step to handle performers
            if scene_data.get("performers"):
                performer_ids = []
                for performer in scene_data["performers"]:
                    performer_name = performer["name"]
                    performer_url = performer.get("url")

                    # Search for existing performer
                    existing_performer = self.stash.find_performers(
                        {"name": {"modifier": "EQUALS", "value": performer_name}}
                    )

                    if existing_performer and len(existing_performer) > 0:
                        performer_ids.append(existing_performer[0]["id"])
                    else:
                        # Create the performer if they don't exist
                        new_performer = {"name": performer_name}
                        if performer_url:
                            new_performer["url"] = performer_url

                        created_performer = self.stash.create_performer(new_performer)
                        performer_ids.append(created_performer["id"])

                # Add performer IDs to the update payload
                update_scene["performer_ids"] = performer_ids

            if scene_data.get("studio"):
                studio_name = scene_data["studio"]["name"]
                existing_studio = self.stash.find_studios(
                    {
                        "name": {"modifier": "EQUALS", "value": studio_name},
                        "OR": {"aliases": {"modifier": "EQUALS", "value": studio_name}},
                    }
                )

                if existing_studio and len(existing_studio) > 0:
                    update_scene["studio_id"] = existing_studio[0]["id"]
                    self.write_debug(f"[Debug] using existing studio {existing_studio}")
                else:
                    # Create the studio if it doesn't exist
                    self.write_debug("[Debug] creating new studio")
                    new_studio = {
                        "name": studio_name,
                        "url": scene_data["studio"]["url"]
                        if scene_data["studio"].get("url")
                        else None,
                    }
                    created_studio = self.stash.create_studio(new_studio)
                    update_scene["studio_id"] = created_studio["id"]

            self.write_debug(f"[Debug] Scene update payload: {update_scene}")

            try:
                self.stash.update_scene(update_scene)
                self.to_screen("[Info] Scene updated with scraped metadata.")
            except Exception as e:
                self.to_screen(f"[Error] Error updating scene metadata: {str(e)}")

        except Exception as e:
            self.to_screen(f"[Error] Unexpected error during processing: {str(e)}")

        return [], info

    def _scrape_scene_by_url(self, url):
        query = """
        query scrapeSceneByURL($url: String!) {
            scrapeSceneURL(url: $url) {
                title
                date
                details
                tags {
                    name
                }
                performers {
                    name
                    url
                }
                studio {
                    name
                    url
                }
            }
        }
        """
        variables = {"url": url}
        try:
            self.write_debug(
                f"[Debug] Sending GraphQL scrapeSceneByURL query for URL: {url}"
            )
            response = self.stash.call_GQL(query, variables)
            self.write_debug(f"[Debug] Full GraphQL response: {response}")

            # Adjust the response check to accommodate both formats
            if response and "data" in response and isinstance(response["data"], dict):
                scrape_scene_data = response["data"].get("scrapeSceneURL")
            elif response and "scrapeSceneURL" in response:
                scrape_scene_data = response["scrapeSceneURL"]
            else:
                scrape_scene_data = None

            # if scrape_scene_data is None:
            #     self.to_screen(
            #         "[Error] 'scrapeSceneURL' field missing or is None in GraphQL response."
            #     )
            #     self.write_debug(f"[Debug] Response structure: {response}")
            #     return None

            # Add detailed debug messages to understand what we received
            if scrape_scene_data:
                self.write_debug(f"[Debug] Scraped scene data: {scrape_scene_data}")
                return scrape_scene_data
            else:
                self.to_screen(
                    "[Error] GraphQL response contained 'scrapeSceneURL' but it was empty."
                )
                self.write_debug(
                    f"[Debug] 'scrapeSceneURL' content: {scrape_scene_data}"
                )
                return None
        except Exception as e:
            self.to_screen(f"[Error] Error in scraping scene by URL: {str(e)}")
            return None

    def _get_paths(self, info):
        absolute_path = str(Path(info["filepath"]).absolute())
        if self.searchpathoverride != "":
            if absolute_path.startswith(self.searchpathoverride):
                self.write_debug("[Debug] Removing searchpathoverride from filepath")
                filepath = absolute_path.replace(self.searchpathoverride, "", 1)
                dirpath = str(Path(filepath).parent)
                return filepath, dirpath
            else:
                self.write_debug("[Debug] prepending searchpathoverride to filepath")
                filepath = self.searchpathoverride + absolute_path
                dirpath = str(Path(filepath).parent)
                return filepath, dirpath
        else:
            filepath = info["filepath"]
            dirpath = str(Path(info["filepath"]).parent)
            return filepath, dirpath

    def _scan_path(self, path: str):
        self.to_screen(f"[Info] Scanning metadata on path: {path}")
        try:
            stash_meta_job = self.stash.metadata_scan(
                paths=path,
                flags={
                    "scanGenerateCovers": False,
                    "scanGeneratePreviews": False,
                    "scanGenerateImagePreviews": False,
                    "scanGenerateSprites": False,
                    "scanGeneratePhashes": False,
                    "scanGenerateThumbnails": False,
                    "scanGenerateClipPreviews": False,
                },
            )
            while True:
                job_status = self.stash.find_job(stash_meta_job)
                self.write_debug(f"[Debug] Metadata scan job status: {job_status}")
                if job_status["status"] == "FINISHED":
                    break
                elif job_status["status"] == "FAILED":
                    raise Exception("Metadata scan job failed")
                sleep(0.5)
        except Exception as e:
            raise Exception(f"Error during metadata scan: {e}")

    def _search_scene_by_path(self, filepath: str):
        # Step 5: Find the newly created scene
        self.write_debug(f"[Debug] Looking for scene with path: {filepath}")
        scene = self.stash.find_scenes(
            {"path": {"modifier": "EQUALS", "value": filepath}}
        )
        self.write_debug(f"[Debug] Scene search result: {scene}")
        if not scene or len(scene) == 0:
            raise Exception("No scene found")
        return scene
