import random
from os.path import join, dirname

import requests
from json_database import JsonStorageXDG

from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class RetroTVSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.MOVIE]
        self.skill_icon = self.default_bg = join(dirname(__file__), "ui", "retrotv_icon.jpg")
        self.archive = JsonStorageXDG("RetroTV", subfolder="OCP")
        super().__init__(*args, **kwargs)

    def initialize(self):
        self._sync_db()
        self.load_ocp_keywords()

    def load_ocp_keywords(self):
        title = []
        genre = ["retro", "classic", "vintage"]

        for url, data in self.archive.items():
            t = data["title"].split("|")[0].split("(")[0].strip().split(",")[0].split("-")[0].lstrip("'").rstrip("'")
            if '"' in t:
                t = t.split('"')[1]
            if ":" in t:
                t1, t2 = t.split(":")
                title.append(t1.strip())
                title.append(t2.strip())
            title.append(t.strip())

        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_name", title)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "film_genre", genre)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_streaming_provider",
                                  ["Retro TV",
                                   "RetroTV"])

    def _sync_db(self):
        bootstrap = "https://github.com/JarbasSkills/skill-retrotv/raw/dev/bootstrap.json"
        data = requests.get(bootstrap).json()
        self.archive.merge(data)
        self.schedule_event(self._sync_db, random.randint(3600, 24 * 3600))

    def get_playlist(self, score=50, num_entries=25):
        pl = self.featured_media()[:num_entries]
        return {
            "match_confidence": score,
            "media_type": MediaType.MOVIE,
            "playlist": pl,
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "image": self.skill_icon,
            "bg_image": self.default_bg,
            "title": "Retro TV (Movie Playlist)",
            "author": "RetroTV"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = 15 if media_type == MediaType.MOVIE else 0
        entities = self.ocp_voc_match(phrase)

        title = entities.get("movie_name")
        skill = "movie_streaming_provider" in entities  # skill matched

        base_score += 30 * len(entities)

        if title:
            base_score += 30
            candidates = [video for video in self.archive.values()
                          if title.lower() in video["title"].lower()]
            for video in candidates:
                yield {
                    "title": video["title"],
                    "author": video["author"],
                    "match_confidence": min(100, base_score),
                    "media_type": MediaType.MOVIE,
                    "uri": "youtube//" + video["url"],
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": video["thumbnail"]
                }

        if skill:
            yield self.get_playlist()

    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "image": video["thumbnail"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": "youtube//" + video["url"],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "bg_image": video["thumbnail"],
            "skill_id": self.skill_id
        } for video in self.archive.values()]


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = RetroTVSkill(bus=FakeBus(), skill_id="t.fake")
    for r in s.search_db("i wanna watch Sherlock Holmes", MediaType.MOVIE):
        print(r)
        # {'title': 'Sherlock Holmes | The House of Fear | Full Classic Mystery Crime Movie In HD | Retro Central', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=QqWJSfwIO4U', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/QqWJSfwIO4U/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/QqWJSfwIO4U/sddefault.jpg'}
        # {'title': 'Sherlock Holmes and the Scarlet Claw | Full Classic Movie in HD! | Basil Rathbone | Nigel Bruce', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=4jJC9mIh0PA', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/4jJC9mIh0PA/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/4jJC9mIh0PA/sddefault.jpg'}
        # {'title': 'Sherlock Holmes And The Secret Weapon | Full  Classic  Movie in HD | Retro TV', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=yBxCuah5tOw', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/yBxCuah5tOw/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/yBxCuah5tOw/sddefault.jpg'}
        # {'title': 'Sherlock Holmes: Terror By Night | Basil Rathbone |  Full Restored Movie in HD! | Retro Central', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=ug2nRua0V14', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/ug2nRua0V14/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/ug2nRua0V14/sddefault.jpg'}
        # {'title': 'Sherlock Holmes and the Spider Woman | Basil Rathbone | Nigel Bruce | Full Classic Movie in HD!', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=8LcqAn0PIrg', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/8LcqAn0PIrg/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/8LcqAn0PIrg/sddefault.jpg'}
        # {'title': 'Sherlock Holmes and the Pearl of Death | Basil Rathbone | Nigel Bruce | Full Restored Movie in HD!', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=AgGTUJOHo9E', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/AgGTUJOHo9E/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/AgGTUJOHo9E/sddefault.jpg'}
        # {'title': 'Sherlock Holmes and the Voice of Terror | Full Classic Movie in HD | Retro TV', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=o5IkYSXMDig', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/o5IkYSXMDig/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/o5IkYSXMDig/sddefault.jpg'}
        # {'title': 'Sherlock Holmes and the Woman In Green | Full Restored Classic Action War Movie in HD! | RC', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=WVKdO2XR4ls', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/WVKdO2XR4ls/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/WVKdO2XR4ls/sddefault.jpg'}
        # {'title': 'Sherlock Holmes in Washington | Full Classic Action Movie | Retro Central', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=iqcdpHMb6Tc', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/iqcdpHMb6Tc/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/iqcdpHMb6Tc/sddefault.jpg'}
        # {'title': 'Sherlock Holmes Faces Death | Full Classic Movie in HD | Crime Mystery | Retro Central', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=4pi2-_0WPNc', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/4pi2-_0WPNc/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/4pi2-_0WPNc/sddefault.jpg'}
        # {'title': 'Sherlock Holmes: Pursuit to Algiers | Full Classic Action Movie | Retro Central', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=xmt_lX6rUrs', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/xmt_lX6rUrs/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/xmt_lX6rUrs/sddefault.jpg'}
        # {'title': 'Sherlock Holmes: The Hound of the Baskervilles | Full Classic Movie in HD!', 'author': 'Retro Central', 'match_confidence': 75, 'media_type': <MediaType.MOVIE: 10>, 'uri': 'youtube//https://youtube.com/watch?v=zmF1BAT23yo', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/zmF1BAT23yo/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/zmF1BAT23yo/sddefault.jpg'}
