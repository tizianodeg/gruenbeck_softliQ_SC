# Gruenbeck SoftliQ SC

This integration uses the local interface from the SoftliQ Device called mux.
This interface is only available for the SC and MC models. E.g. SC18 SC28
It is not available for SD devices. 

The integration is still in alpha phase and was tested an a SC18 Device. 

## Configuration

It supports the UI the config flow, after adding the integration in the Setting - Integration ribbon, you will be asked to supply a name and the IP-Address of your device. 

## Current limitations
1. Only reading values is implemented
1. Not all available sensors are displayed

## Available Sensors:

| Sensor | example |
| ------------- | ------------- |
| Average consumption over the last 3 day| 0,10| 
| Capacity number| 6,0 %| 
| Consumption capacity rate| 1,9| 
| Current flow| 0,00 m³| 
| Current regeneration step|No regeneration| 
| days until the next maintenance| 0 d| 
| Flow peak value| 1,22 m³/h| 
| Last Error| Fill salt tablets in the salt tank| 
| Last Error days old| 1.283 d| 
| Last regeneration| 23| 
| Percentage regeneration| 80 %| 
| Raw water hardness| 20,0| 
| remaining capacity| 0,25 m³| 
| Remaining time/quantity regeneration step| 0,0 min| 
| Salt consumption per year| Unbekannt| 
| Salt range in days| 99 d| 
| Soft water volume meter| 211 m³| 
| Software Version| V01.01.02| 
| Total flow| Unbekannt| 
| Water consumption yesterday| 52 L| 