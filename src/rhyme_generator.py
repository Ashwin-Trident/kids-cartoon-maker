from dataclasses import dataclass
from typing import List, Optional
import random


@dataclass
class RhymeScene:
    text: str
    scene_description: str
    duration_seconds: float = 4.0


@dataclass
class Rhyme:
    name: str
    title: str
    scenes: List[RhymeScene]
    style: str = "cute cartoon for kids, bright colors, simple shapes, child-friendly, no text"


RHYMES = {
    "twinkle": Rhyme(
        name="twinkle", title="Twinkle Twinkle Little Star",
        scenes=[
            RhymeScene("Twinkle, twinkle, little star,", "a cute glowing yellow star with big eyes in a dark blue night sky, cartoon style"),
            RhymeScene("How I wonder what you are!", "a small child looking up at the night sky with wonder, cartoon style, colorful"),
            RhymeScene("Up above the world so high,", "a tiny star high above fluffy clouds and the earth below, cartoon style"),
            RhymeScene("Like a diamond in the sky.", "a sparkling diamond-shaped star shining in space, kawaii cartoon style"),
            RhymeScene("Twinkle, twinkle, little star,", "a happy smiling star with sparkles all around, bright colorful cartoon"),
            RhymeScene("How I wonder what you are!", "a child waving goodnight to a smiling star, cozy cartoon night scene"),
        ],
    ),
    "humpty": Rhyme(
        name="humpty", title="Humpty Dumpty",
        scenes=[
            RhymeScene("Humpty Dumpty sat on a wall,", "a cute round egg character with a happy face sitting on a brick wall, cartoon style"),
            RhymeScene("Humpty Dumpty had a great fall.", "a round egg character falling off a wall with surprised expression, cartoon style"),
            RhymeScene("All the king's horses and all the king's men,", "cartoon toy horses and royal guards rushing to help, colorful kids style"),
            RhymeScene("Couldn't put Humpty together again.", "a sad round egg character with bandages, surrounded by concerned friends, cartoon style"),
        ],
    ),
    "itsy": Rhyme(
        name="itsy", title="Itsy Bitsy Spider",
        scenes=[
            RhymeScene("The itsy bitsy spider climbed up the water spout,", "a tiny cute smiling spider climbing a drainpipe, cartoon style bright colors"),
            RhymeScene("Down came the rain and washed the spider out.", "cartoon rain falling on a tiny spider sliding down, cute expression"),
            RhymeScene("Out came the sun and dried up all the rain,", "a big smiling cartoon sun shining in a blue sky with rainbow"),
            RhymeScene("And the itsy bitsy spider climbed up the spout again!", "a happy determined little spider climbing up again, triumphant pose, cartoon"),
        ],
    ),
    "baa": Rhyme(
        name="baa", title="Baa Baa Black Sheep",
        scenes=[
            RhymeScene("Baa baa black sheep, have you any wool?", "a cute fluffy black sheep in a green meadow, cartoon style"),
            RhymeScene("Yes sir, yes sir, three bags full!", "a cheerful black sheep with three big bags of wool, cartoon style"),
            RhymeScene("One for the master, one for the dame,", "cartoon characters of a farmer and a lady receiving wool bags"),
            RhymeScene("And one for the little boy who lives down the lane.", "a happy little cartoon boy receiving a bag of wool on a country lane"),
        ],
    ),
    "mary": Rhyme(
        name="mary", title="Mary Had a Little Lamb",
        scenes=[
            RhymeScene("Mary had a little lamb,", "a cute cartoon girl with a tiny fluffy white lamb, green meadow background"),
            RhymeScene("Its fleece was white as snow,", "a fluffy white cartoon lamb glowing softly in sunlight"),
            RhymeScene("And everywhere that Mary went,", "a cartoon girl skipping through a colorful field of flowers"),
            RhymeScene("The lamb was sure to go!", "a little lamb happily following a girl, cartoon, big eyes, bright colors"),
            RhymeScene("It followed her to school one day,", "a cartoon lamb peeking through a school window, funny expression"),
            RhymeScene("Which was against the rules!", "cartoon children laughing at a fluffy lamb in a classroom, fun scene"),
        ],
    ),
    "jack": Rhyme(
        name="jack", title="Jack and Jill",
        scenes=[
            RhymeScene("Jack and Jill went up the hill,", "two cartoon children climbing a green hill with a pail, sunny day"),
            RhymeScene("To fetch a pail of water.", "cartoon kids carrying a wooden bucket up a hill, cute style"),
            RhymeScene("Jack fell down and broke his crown,", "cartoon boy tumbling down a grassy hill, funny surprised face"),
            RhymeScene("And Jill came tumbling after!", "cartoon girl rolling down a hill after her brother, both laughing"),
        ],
    ),
    "hickory": Rhyme(
        name="hickory", title="Hickory Dickory Dock",
        scenes=[
            RhymeScene("Hickory dickory dock,", "a cute cartoon grandfather clock with big eyes and a smile, cartoon style"),
            RhymeScene("The mouse ran up the clock.", "a tiny cartoon mouse running up a tall clock, cartoon style bright"),
            RhymeScene("The clock struck one,", "a cartoon clock with one finger raised, a bell ringing, cute style"),
            RhymeScene("The mouse ran down, hickory dickory dock!", "a tiny mouse sliding down a clock laughing, colorful cartoon"),
        ],
    ),
}


def get_rhyme(name: str) -> Optional[Rhyme]:
    return RHYMES.get(name.lower())

def get_random_rhyme() -> Rhyme:
    return random.choice(list(RHYMES.values()))

def get_rhyme_from_text(text: str, title: str = "My Rhyme") -> Rhyme:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    prompts = [
        "cute cartoon animals in a colorful forest, bright colors, child-friendly",
        "cartoon sunshine over a happy village, kids playing, bright colors",
        "cartoon flowers, butterflies, and bees in a garden, child-friendly",
        "cute cartoon clouds and rainbows in a bright sky",
        "cartoon children playing in a park, colorful, happy scene",
        "a magical cartoon treehouse in a colorful forest",
    ]
    scenes = [RhymeScene(text=line, scene_description=prompts[i % len(prompts)]) for i, line in enumerate(lines)]
    return Rhyme(name="custom", title=title, scenes=scenes)

def list_rhymes() -> List[str]:
    return list(RHYMES.keys())
