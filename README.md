<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/fb58da044365d0beac8132a96daffff3d9c79980/imgs/logo.png" alt="alt text" width="14%"></p>

# RobInHood
RobInHood is an open-source software framework for running automated chemistry experiments inside a standard laboratory fume hood. Traditional fume hoods are designed for human chemists, which makes automation in these spaces challenging. RobInHood addresses this by combining a robotic arm with modular hardware stations and a unified Python control layer.

The software is written in Python and acts as the central coordinator for all hardware components, including laboratory instruments, robotic motion, and custom-built devices. By providing a flexible and extensible architecture, RobInHood enables complex experimental workflows to be automated, reproduced, and adapted to new chemical processes.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/d83860dc0c4db4c357c87538e46461c3c9a04604/imgs/robinhood.png" alt="alt text" width="100%"></p>

Overview of the RobInHood platform.
- Left-hand side: liquid reagent reservoirs; a module for dispensing magnetic stir bars; syringe pump assemblies with a dispensing nozzle; and a motorized vial holder positioned above a protective drip tray.
-  Central section: an automated capping and decapping unit; vial storage racks; an imaging and illumination enclosure; the Panda robotic arm; storage for solid-dispensing cartridges used by the Quantos system; filtration cartridge storage; a heating and stirring hotplate; and the Quantos solid dispensing unit.
- Right-hand side: the filtration station, comprising a receiving funnel and flask, a robotic pouring arm, and a vial holder with an associated dispensing head.

## Key Features

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
## Software Architecture 

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/1539644cdfc47cc909d748a841c5aea4363c5222/imgs/software.png" alt="alt text" width="80%"></p>

## Demo

[![Alt Text](http://img.youtube.com/vi/VVtX8a-V6tc/0.jpg)](https://www.youtube.com/watch?v=VVtX8a-V6tc)

## Setup

Clone this repo to your PC and run `pip install .` from the repository folder.

## Examples

RobInHood has been used for several workflows, including porosity screning, the synthesis of CC3, and Phthalimide, which can be a accesed here: 

1. Posority
2. CC3
3. Phthalimide


## Paper

