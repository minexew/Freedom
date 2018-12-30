# Freedom
Reverse engineering of Freedom Fighters (2003) and possibly other Glacier engine games

[![screenshot](https://raw.githubusercontent.com/minexew/Freedom/master/_images/render.jpg)](https://raw.githubusercontent.com/minexew/Freedom/master/_images/render.jpg)

## File formats in map data

### BUF
    - no header
    - ASCII resource names throughout
    - identifiers at the end
    - random data referenced externally?
    - not present in ErrorMessages

    - contains GMS instance names
    - contains GMS instance auxiliary buffers (not understood)

### GMS - entities
    - compressed
    - cross-refs to PRM - mostly understood, able to render entire scene into .obj
    - refers to function names (script not figured out yet)

### LOC - hierarchical localization data
    - fully understood
    - not present in ErrorMessages

### OCT - ?

### PRM - object geometry
    - we're able to enumerate models
    - dump OBJs with correct vertex positions and load those into Blender
    - doesn't describe model placement in world (see GMS)
    - a lot of questions remain
    - doesn't seem to contain world terrain (??)

### RMC - ?
### RMI - ?
### SGP - ?
### SND - ?
### SUP - ?

### TEX - textures
    - texdump managed to parse everything we tried
    - also contains reference to WAV files - this part is not understood

### ZGF - compressed font collection
    - able to reliably decompress
    - unable to reliably tell font boundaries
    - (probably not very interesting)

### xtr - custom format to help mapping file layouts and find gaps in understood data
