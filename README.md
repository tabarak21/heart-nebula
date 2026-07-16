# Heart Nebula Composition 3D

This version does not draw a geometric heart.

Instead, it generates:
- two irregular red gas lobes
- a dark central cavity
- broken outer clouds
- a lower gas tail
- crimson and rose emission filaments
- internal dust
- embedded stars
- foreground 3D stars
- continuous zoom movement

## Run

```bash
pip install -r requirements.txt
python main.py
```

The first run may take several seconds while the nebula is generated.


## Polish update

- realistic brightness distribution
- true soft bloom for only the brightest stars
- rare subtle diffraction flares
- slow natural twinkling
- faint procedural dark cosmic dust


## Depth-link update

- far stars share nearly the same camera motion as the nebula
- mid-space stars move moderately
- near stars provide foreground parallax
- star brightness and size vary by depth layer
- the nebula and embedded stars now read as one spatial scene


## Gravitational ripple interaction


- Left click creates a soft expanding ripple.
- Stars are pushed according to their depth layer.
- Near stars react more strongly than far stars.
- The nebula receives a very subtle linked displacement.
- No particle explosion or cosmic dust burst is used.
 <img width="1023" height="1537" alt="Heart nebula" src="https://github.com/user-attachments/assets/ad191b8c-41fa-4fb3-a2bd-da203a01503b" />
