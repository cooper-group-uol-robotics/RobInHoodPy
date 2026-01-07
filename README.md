<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/fb58da044365d0beac8132a96daffff3d9c79980/imgs/logo.png" alt="alt text" width="14%"></p>

# RobInHood
RobInHood is an open-source software framework for running automated chemistry experiments inside a standard laboratory fume hood. Traditional fume hoods are designed for human chemists, which makes automation in these spaces challenging. RobInHood addresses this by combining a robotic arm with modular hardware stations and a unified Python control layer.

The software is written in Python and acts as the central coordinator for all hardware components, including laboratory instruments, robotic motion, and custom-built devices. By providing a flexible and extensible architecture, RobInHood enables complex experimental workflows to be automated, reproduced, and adapted to new chemical processes.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/154929987a24251540495ce667d4e8ca60c47937/imgs/robinhood.png" alt="alt text" width="100%"></p>

Overview of the RobInHood platform.
(A) Left-hand side: liquid reagent reservoirs; a module for dispensing magnetic stir bars; syringe pump assemblies with a dispensing nozzle; and a motorized vial holder positioned above a protective drip tray.
(B) Central section: an automated capping and decapping unit; vial storage racks; an imaging and illumination enclosure; the Panda robotic arm; storage for solid-dispensing cartridges used by the Quantos system; filtration cartridge storage; a heating and stirring hotplate; and the Quantos solid dispensing unit.
(C) Right-hand side: the filtration station, comprising a receiving funnel and flask, a robotic pouring arm, and a vial holder with an associated dispensing head.

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
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/154929987a24251540495ce667d4e8ca60c47937/imgs/software.png" alt="alt text" width="100%"></p>

## Demo

[![Alt Text](http://img.youtube.com/vi/VVtX8a-V6tc/0.jpg)](https://www.youtube.com/watch?v=VVtX8a-V6tc)

## Setup

Clone this repo to your PC and run `pip install .` from the repository folder.

## Examples

RobInHood has been used for several workflows, including porosity screning, the synthesis of CC3, and Phthalimide, which can be a accesed here: 

1. Posority
2. CC3
3. Phthalimide

## Platform Operation Manual

In the boot menu, select  Advanced options for Ubuntu.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/kernel_1.png" alt="alt text" width="60%"></p>

In the new menu, select 5.9.1-rt20. This is necessary for the computer to control the Panda robot.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/kernel_2.png" alt="alt text" width="60%"></p>

To verify that the correct kernel was selected,  type: 
```  
uname -r
```
<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/kernel_3.png" alt="alt text" width="60%"></p>

## Panda robot

Turn on the switch of the station.
<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/panda_00.png" alt="alt text" width="60%"></p>
  
Open a browser, and go to "HTTP://172.16.0.2" in a new tab.

Click the unlock button and then click Open.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/panda_1.png" alt="alt text" width="60%"></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/panda_2.png" alt="alt text" width="60%"></p>

Once the robot breaks have been unlocked, the robot's light will change to purple if the emergency button is active and to blue if the emergency button is unpressed.  

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/panda_3.png" alt="alt text" width="60%"></p>

Emergency stop button:

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/panda_01.png" alt="alt text" width="60%"></p>

To turn off the robot, it is necessary first to click the lock button. 
Then, click the shutdown button and click Yes. Finally, wait until a pop-up window indicates that it is safe to turn off the system.

## Setting up a working environment

Open a terminal and navigate to the RobInHood directory with the following:

```
cd ~\RobinHoodPy
code .
``` 

From the menu, click on terminal and then click on New Terminal.

It is necessary to activate a conda environment. To do so, type:

```conda activate robostackenv38```

## Manipulating vials

The current setup supports the storage of up to 16 vials. The robot can take the vial to the vial holder of the xCalibur pump, the plate of the IKA station, the Quantos station, and the other way around for all the cases.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/rack.png" alt="alt text" width="60%"></p>

These are some of the instructions that can be executed:

```
station.vial_rack_to_quantos(vial_number=1)
station.vial_rack_to_ika(vial_number=9, ika_slot_number=5)
station.vial_ika_to_rack(ika_slot_number=6, vial_number=22)
```

## Mounting/Unmounting Cartridges in Quantos Mettler

Currently, the setup supports up to three cartridges. 

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/cartridges.png" alt="alt text" width="60%"></p>

These are some of the instructions that can be executed:

```
station.pick_and_place_cartridge_in_quantos(cartridge_number = 1)
```

```
station.quantos_dosing(quantity=10)
```

```
station.pick_and_place_cartridge_in_holder(cartridge_number= 1)
```

## Putting vials on  the IKA station plate

The IKA station place can contain up to 12 vials.

<p align="center">
  <img src="https://raw.githubusercontent.com/FranciscoMunguiaGaleano/RobInHoodImgs/3d0e05901ff619ef1c97fcd88b28760e17fe576a/imgs/ika.png" alt="alt text" width="60%"></p>

These are some of the instructions that can be executed: 

```
station.ika.start_stirring()
station.timer.set_timer(hours=0,min=1, sec=15)
station.timer.start_timer()
station.ika.stop_stirring()
```

## Liquid dispensing


These are some of the instructions that can be executed: 
```
station.push_pump()
station.pump_inyect(input_source="I3",output="I2",quantity=2000,repeat=2)
station.pump_inyect(input_source="I3",output="I1",quantity=2000,repeat=2)
station.pull_pump()
```

## Filatrtion setup 

## Paper

