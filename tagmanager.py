from config import Config 
from datetime import datetime

class TagManager:
    def __init__(self,config: Config | None = None):
        self.config = config or Config()
        # Additional initialization code can go here 

#-------- ADD TAGS OR EDIT TAGS ----------
    def merge_tags(self, initial_tags: str | None, tags: list[str]) -> str:
        base = [t.strip() for t in (initial_tags or "").split(",") if t.strip()]
        incoming = [t.strip() for t in tags if t.strip()]

        merged = base[:]  # start with existing tags
        for t in incoming:
            if t not in merged:
                merged.append(t)

        return ",".join(merged)
#----- CHECK FOR DATE ------   
    def is_datetime_string(self, s: str) -> bool:
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False

    # incoming_text is the user's input string like:
    # "2020-11-13 10:00:00,Apple,iPhone 7"
    # returns (new_dt, new_make, new_model) where any can be None meaning "no change"
    def parse_replacements(self, incoming_text: str) -> tuple[str | None, str | None, str | None]:
        parts = [p.strip() for p in (incoming_text or "").split(",")]

        # normalize to 3 slots
        while len(parts) < 3:
            parts.append("")
        if len(parts) > 3:
            parts = parts[:3]  # ignore extras

        dt_s, make, model = parts

        new_dt = dt_s if dt_s and self.is_datetime_string(dt_s) else None
        new_make = make if make else None
        new_model = model if model else None

        return new_dt, new_make, new_model
#--------- DELETE TAGS ---------
    def delete_tags(self,initial_tags: str | None, tags: list[str]):
        if initial_tags:
            base = [t.strip() for t in initial_tags.split(",") if t.strip()]
        incoming = [t.strip() for t in tags if t.strip()]
        new_tags = [] + base
        for i in range(len(incoming)):
            if incoming[i] in base:
                new_tags.remove(incoming[i])
            else:
                pass
        return ",".join(new_tags)

#----- AT MAIN -------
if __name__ == "__main__":
    config = Config("config.yaml")
    tag_manager = TagManager(config)
    
