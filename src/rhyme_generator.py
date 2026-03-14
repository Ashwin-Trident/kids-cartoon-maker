import random


class Scene:
    def __init__(self, text):
        self.text = text


characters = ["Tom the Cat", "Milo the Mouse", "Benny the Bunny", "Lulu the Duck"]
places = ["kitchen", "garden", "park", "playground"]
actions = ["ran after", "jumped over", "slipped on", "hid behind"]
objects = ["a banana", "a cookie", "a toy car", "a ball"]


def generate_story():

    c1 = random.choice(characters)
    c2 = random.choice([c for c in characters if c != c1])

    place = random.choice(places)

    story = [
        f"One sunny day {c1} met {c2} in the {place}.",
        f"Suddenly {c2} {random.choice(actions)} {random.choice(objects)}.",
        f"{c1} quickly {random.choice(actions)} {c2}.",
        f"They both laughed and ran around the {place}.",
        f"In the end they shared {random.choice(objects)} happily."
    ]

    return [Scene(s) for s in story]
