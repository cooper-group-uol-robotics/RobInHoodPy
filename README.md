<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/fb58da044365d0beac8132a96daffff3d9c79980/imgs/logo.png" alt="alt text" width="22%"></p>

-----

RobInHood is an open-source software framework for running automated chemistry experiments inside a standard laboratory fume hood. Traditional fume hoods are designed for human chemists, which makes automation in these spaces challenging. RobInHood addresses this by combining a robotic arm with modular hardware stations and a unified Python control layer.

The software is written in Python and acts as the central coordinator for all hardware components, including laboratory instruments, robotic motion, and custom-built devices. By providing a flexible and extensible architecture, RobInHood enables complex experimental workflows to be automated, reproduced, and adapted to new chemical processes.

### Key Features

1. 🧪 Fume-hood–compatible automation
Designed to operate entirely within a standard laboratory fume hood.

2. 🤖 Robotic manipulation
Precise control of a robotic arm for handling vessels, tools, and samples.

3. ⚙️ Integrated laboratory hardware
Native support for commercial instruments such as pumps, hotplates, and powder dispensers.

4. 🔌 Custom hardware control
Serial communication with Arduino-based electronic and pneumatic systems.

5. 🧠 Python-based orchestration
Modular, readable, and extensible workflow control written entirely in Python.

6. 🔁 Reproducible workflows
Enables repeatable and automated execution of complex chemical procedures.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/d83860dc0c4db4c357c87538e46461c3c9a04604/imgs/robinhood.png" alt="alt text" width="100%"></p>

### Overview of the RobInHood platform.
- Left-hand side: liquid reagent reservoirs; a module for dispensing magnetic stir bars; syringe pump assemblies with a dispensing nozzle; and a motorized vial holder positioned above a protective drip tray.
-  Central section: [an automated capping and decapping unit](https://link.springer.com/chapter/10.1007/978-3-032-01486-3_35); vial storage racks; an imaging and illumination enclosure; the Panda robotic arm; storage for solid-dispensing cartridges used by the Quantos system; filtration cartridge storage; a heating and stirring hotplate; and the Quantos solid dispensing unit.
- Right-hand side: the filtration station, comprising a receiving funnel and flask, a robotic pouring arm, and a vial holder with an associated dispensing head.


## Software Architecture 

RobInHood uses a Python-based control stack to coordinate robotic motion, commercial laboratory instruments, and custom hardware modules. Python serves as the central orchestration layer due to its flexibility and strong support for scientific and hardware-control libraries.

Commercial devices (e.g. IKA hotplates, Tecan XCalibur pumps, and the Mettler Toledo Quantos) are integrated via drivers built on the [pylabware](https://github.com/croningp/pylabware.git)  framework. Custom electronic, pneumatic, and motorized components are controlled through serial communication with embedded Arduino microcontrollers. The robotic arm is operated using the FrankaX Python library.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/1539644cdfc47cc909d748a841c5aea4363c5222/imgs/software.png" alt="alt text" width="80%"></p>

### Configuration and Workflows

Reagents and system configuration are defined using simple .csv files:

- dispense.csv — liquid dispensing module

- filt.csv — filtration module liquids

- quantos.csv — solid dispensing cartridges

These files store reagent identities, locations, and metadata, and are automatically cross-checked at runtime to prevent setup errors. Active reagent states are cached as JSON files to reduce setup time between runs.

Experimental workflows are defined by combining reusable Python methods provided by the central RobInHood class. Sample-specific parameters (e.g. reagent amounts or vial positions) can be supplied via samples.csv files or directly in workflow scripts. This modular design allows new workflows to be created or modified by updating configuration files rather than rewriting control code.

## Demo

This demo shows an end-to-end automated mock workflow executed by the RobInHood platform inside a standard laboratory fume hood, aiming to show all the features available in RobInHood.

The system begins with sample preparation, where a solid reagent is dispensed into a vial with repeated weighing for accuracy, followed by automated addition of liquids and a stir bar. The vial is then capped and stirred.

Next, the platform performs automated filtration. The filtration system is conditioned with water, the sample vial is decapped and transferred to a pouring arm, and the contents are poured through a filter into a fresh vial. The filtered sample is capped and stored, and the filtration setup is rinsed for reuse.

Finally, the sample analysis stage places the filtered vial into a lightbox for imaging before returning it to storage.

<p align="center">
  <a href="https://www.youtube.com/watch?v=VVtX8a-V6tc">
    <img src="http://img.youtube.com/vi/VVtX8a-V6tc/0.jpg" alt="RobInHood Demo Video">
  </a>
</p>


## Setup

### 1. Create a virtual environment (recommended)

We strongly recommend using a virtual environment to avoid dependency conflicts.

```
python -m venv venv
source venv/bin/activate        # On Linux/macOS
venv\Scripts\activate           # On Windows
```

### 2. Install the instrument drivers (modified pylabware)
This project relies on instrument drivers based on the open-source
[pylabware](https://github.com/croningp/pylabware.git) repository developed by the Cronin Group.

We use a modified internal fork of pylabware that includes additional drivers for:

- Mettler Toledo Quantos

- XCalibur syringe pump

- Tricontinent syringe pump

- IKA hotplate

Due to licensing and authorship constraints, this modified version cannot be publicly distributed.
***Access to the drivers can be provided upon request.***

Once access is granted, install the modified pylabware locally:

```
pip install .
(from within the modified pylabware repository)
```
### 3. Install this repository’s dependencies and package
From the root of this repository, install the required dependencies:

```
pip install -r requirements.txt
pip install .
```
## Examples

RobInHood has been used for several workflows, including porosity screening, the synthesis of CC3, and phthalimide chemistry. The workflow scripts and examples can be accessed in the [RobInHoodWorkflows repository](https://github.com/cooper-group-uol-robotics/RobInHoodWorkflows.git):

1. [**Porosity Screening**](https://github.com/cooper-group-uol-robotics/RobInHoodWorkflows/tree/ad86fb82fad053bc43498891f581f58269986caf/Porosity_workflow)  
2. [**CC3 Synthesis**](https://github.com/cooper-group-uol-robotics/RobInHoodWorkflows/tree/ad86fb82fad053bc43498891f581f58269986caf/CC3_synth_workflow)  
3. [**Phthalimide Chemistry**](https://github.com/cooper-group-uol-robotics/RobInHoodWorkflows/tree/ad86fb82fad053bc43498891f581f58269986caf/Phthalimide_workflow) 


## Acknowledgment
<details>
  <summary><b>Paper</b></summary>

  Longley L., Munguia-Galeano F., Han Y., Clowes R., Vijayakrishnan S., Edwards A., Pizzuto G., Fakhruldeen H., and Cooper A.  
  [**RobInHood: A Robotic Chemist in a Fume Hood**](https://chemrxiv.org/engage/chemrxiv/article-details/695e8cb7fc9dac0f376baaad).  
  *ChemRxiv preprint*, 2026. https://doi.org/10.26434/chemrxiv-2026-s2619  
  *(This content is a preprint and has not been peer-reviewed.)*

  ```bibtex
  @article{longley2026RobInHood,
    title   = {RobInHood: A Robotic Chemist in a Fume Hood},
    author  = {Longley, L. and Munguia-Galeano, F. and Han, Y. and Clowes, R. and Vijayakrishnan, S. and Edwards, A. and Pizzuto, G. and Fakhruldeen, H. and Cooper, A.},
    journal = {ChemRxiv},
    year    = {2026},
    doi     = {10.26434/chemrxiv-2026-s2619},
    note    = {Preprint, not peer-reviewed}
  }


