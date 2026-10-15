# Perceptual unit

A small experimental generic model of memory built from perceptions that hold energy and move between planes. It is built step by step and every step is tested. Nothing here depends on a language, a word list or a trained model.

## The idea

* A **perception** is an input token (a hash) placed at a position in a plane in a moment with an energy. Its radius is its energy.
* A **plane** is a unit square that holds perceptions. A plane holds at most one perception per token and per moment. A perception never holds more energy than the **peak** of its plane.
* A **cursor** is a point that travels across a plane and reads the perceptions it crosses. A read takes a little energy from the perception. The energy is either given to a perception of another plane born at the same position or destroyed when the cursor has no target.
* After a read the perception is deactivated for that cursor for a while. The cursor neither reads it nor is attracted by it. A cursor can also ignore perceptions younger than a minimum age. The deactivation time is a setting of each cursor. In the shipped config it is the time the cursor needs to travel 1.3 times the diagonal of the plane at its speed.
* A **unit** is a set of planes joined by cursors. A text enters the first plane as one perception per token and as a single event recorded in the current moment. The energy then flows from the short-term plane A to the long-term plane C and the output plane D and fades.
* A **moment** is a window of time opened by the scheduler. Events and links between tokens are counted per moment. A moment is released when it is over and none of its perceptions is alive.
* A **lexicon** gives each token its letters so that two tokens that look alike can be recognised. A plane can optionally pull its perceptions toward similar ones (`relax`) inside a limited radius around their birth position.

All the work is driven by the perceptions. Nothing happens without them. A scheduler runs the planes and the cursors tick by tick under a budget. Each plane visits its perceptions in a pass that can be resumed.

## Run

```
python3 gui/server.py
```

Open http://127.0.0.1:8100/ and type a text. The page shows one canvas per plane. Each perception is a circle at its real radius with its word. Each cursor has its own colour. A small dot in the colour of a cursor appears on every perception that is locked for it. The Reset button builds a fresh unit from the same config.

## Tests

```
python3 -m unittest discover -s tests
```

## Where things are

* `src/` holds the unit: `unit.py`, `plane.py`, `perception.py`, `cursor.py`, `scheduler.py`, `moments.py`, `memory.py`, `lexicon.py`, `relaxation.py` and `validation.py`.
* `gui/` holds the page, its server and `config.json`, the configuration of the unit shown in the page.
* `tests/` holds the tests.

The configuration is validated at startup. It covers the planes (peak, origin radius, relaxation, transfers), the cursors (energy, step, deactivation time, minimum age), the scheduler (tick, budget, moment), the memory and the input energy.

## Status

Work in progress. The settings of `gui/config.json` come from measurements on small corpora and are not final.


*Th6uD1nk*
