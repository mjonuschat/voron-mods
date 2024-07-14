---
title: "Energy Usage Monitoring & Tracking"
description: "How to track energy consumption of print jobs using a Shelly power meter, Moonraker sensors and Mainsail"
summary: ""
date: 2024-07-14T20:15:25Z
lastmod: 2024-07-14T20:15:25Z
draft: false
weight: 810
toc: true
seo:
  title: "" # custom title (optional)
  description: "" # custom description (recommended)
  canonical: "" # custom canonical URL (optional)
  noindex: false # false (default) or true
---

## Introduction

Moonraker's extended data collection capabilities enable seamless integration with additional sensor sources, including power meters. This feature allows for the tracking of energy consumption data within Moonraker's job history component. Leveraging energy monitors like the Shelly 1PM series, you can gain insights into the energy usage per print job. This guide provides a step-by-step walkthrough for setting up a MQTT server to facilitate data exchange between Shelly and Moonraker, as well as configuring Moonraker to poll and store energy consumption data. Additionally, this guide covers the configuration of Mainsail and Moonraker sensors to track energy usage in the job history.

## Prerequisites

- A power meter or sensor capable of publishing measurements to an MQTT server is required. Compatible devices include the Shelly PM series (e.g., [Shelly 1PM Pro](https://www.shelly.com/en/products/shop/shelly-pro-1pm) or [Shelly 1PM Mini](https://www.shelly.com/en/products/shop/shelly-1-pm-mini-gen3)) and [Tasmota](https://tasmota.github.io/docs/)-based devices. Please note that device installation is not covered in this guide.
- The power meter must be configured to operate on the same network as the Raspberry Pi that controls your printer to allow communication and data exchange.
- A recent version of Mainsail installation (minimum version 2.12.0) is also required.

{{< callout context="note" title="Note" icon="outline/info-circle" >}}
This guide assumes the use of a Shelly 1PM device. Please ensure your device is compatible and properly installed before proceeding.
{{< /callout >}}

## MQTT Server

MQTT (Message Queuing Telemetry Transport) is a lightweight, machine-to-machine communication protocol that enables Internet of Things (IoT) components to exchange messages. In this application, the Powermeter utilizes MQTT to periodically publish measurement data, while Moonraker subscribes to these messages to receive the data. To facilitate this communication, we will install an MQTT Server on the Raspberry Pi controlling the 3D printer.

### Installation

Please execute the following commands via SSH to complete the installation.

{{< callout context="note" title="Note" icon="outline/info-circle" >}}
The guide is using [Mosquitto](https://mosquitto.org/) as the MQTT server.
{{< /callout >}}

1. Install the necessary software components by running the following command

   ```bash {title="Installing the Mosquitto server"}
   sudo apt install -y mosquitto mosquitto-clients
   ```

1. Configure the Mosquitto MQTT server to automatically start on system boot

   ```bash {title="Starting Mosquitto on printer startup"}
   sudo systemctl enable mosquitto.service
   ```

### Configuration

To enable the MQTT server to receive messages from the power meter over the network, it is essential to configure the server to listen on a designated network port. The subsequent steps will guide you through the setup process for an unauthenticated (anonymous) connection, ensuring seamless communication between the power meter and the MQTT server.

{{< callout context="danger" title="Important Security Note" icon="outline/alert-triangle" >}}
If you plan to expose your 3D printer or Raspberry Pi to the public internet, it is crucial to implement an authenticated and encrypted connection to ensure secure communication. This guide does not cover authentication and encryption setup. Please refer to the Mosquitto documentation on [Authentication Methods](https://mosquitto.org/documentation/authentication-methods/) and [SSL/TLS Support](https://mosquitto.org/man/mosquitto-conf-5.html) for comprehensive instructions on configuring a secure connection. This will help protect your device and data from unauthorized access.
{{< /callout >}}

1. Execute the following command to access and modify the configuration file

   ```bash {title="Editing the configuration file"}
   sudo nano /etc/mosquitto/mosquitto.conf
   ```

1. Append the following configuration settings to the end of the file

   ```ini {title="mosquitto.conf"}
   listener 1883
   allow_anonymous true
   ```

1. Exit the editor and save the file by pressing **CTRL-X**, then confirm with **Y** and **Enter**
1. Apply the new configuration by restarting Mosquitto

   ```bash {title="Restarting the Mosquitto service"}
   sudo systemctl restart mosquitto
   ```

## Power Meter

Next, configure the power meter to publish measurements at regular intervals to the MQTT server, enabling data exchange and tracking.

### Configuration

1. Identify the IP address of your Raspberry Pi by executing the following command:

   ```bash {title="Determining the primary IP address"}
   hostname -I
   ```

   The resulting output should resemble the following:

   ```text {title="Output"}
   py@voron: $ hostname -I
   198.51.100.60 198.51.100.61 2600:1700:5430:87af::1106 2001:0db8:5dc9:b0ba:f8a8:7e3c:45e2:faab 2001:0db8:5dc9:b0ba:f8a8:7e3c:45e2:faac
   ```

   Take note of the primary IP address, **198.51.100.60**, displayed in the first column of the output. This information is essential for the next steps, so please document it for later use.

   {{< callout context="note" title="Note" icon="outline/info-circle" >}}
   Keep in mind that the actual output may vary due to differences in system settings and configurations.
   {{< /callout >}}

1. Open a web browser and enter the IP address of your Shelly device to access its web-based interface and configure settings.
1. Navigate to **Settings > MQTT** in the **Connectivity** section.
1. Configure the following settings:
    - **Enable**: Checked
    - **Connection type**: No SSL
    - **MQTT Prefix**: my-printer
    - **MQTT Control**: Enabled
    - **Generic status update over MQTT**: Enabled
    - **Server**: IP address of your Raspberry Pi (determined in step 1), followed by `:1883`, for example **198.51.100.60:1883**
    - **Client ID**: my-printer
    - **Username** and **Password**: Leave blank

   ![Shelly MQTT Settings](images/guides/energy-usage-monitoring/shelly-mqtt-settings.png)
1. Click **Save Settings** to apply the changes. A restart of the Shelly might be required.

## Moonraker

Configure Moonraker to integrate additional sensor sources, enabling real-time data tracking in Mainsail and historical data analysis in the job history.

### MQTT Configuration

1. Execute the following command to access and modify the configuration file

   ```bash {title="Editing the Moonraker configuration file"}
   sudo nano ~/printer_data/config/moonraker.conf
   ```

1. Append the following configuration settings to the file to configure Moonraker to receive messages from the MQTT server

   ```ini {title="moonraker.conf"}
   [mqtt]
   address: 127.0.0.1
   enable_moonraker_api: False
   ```

### Sensor Configuration

1. Append the following configuration block to establish a sensor that subscribes to MQTT messages from the Shelly 1PM

   ```ini {title="moonraker.conf"}
   [sensor powermeter]
   type: mqtt
   name: Shelly 1PM
   parameter_power:
     units=W
   parameter_voltage:
     units=V
   parameter_current:
     units=A
   parameter_energy:
     units=kWh
   state_topic: my-printer/status/switch:0
   state_response_template:
     {% set notification = payload|fromjson %}
     {set_result("power", notification["apower"]|float)}
     {set_result("voltage", notification["voltage"]|float)}
     {set_result("current", notification["current"]|float)}
     {set_result("energy", notification["aenergy"]["total"]|float / 1000)}
   ```

   This configuration enables the extraction of key data points from Shelly 1PM status updates, including:

    - Current mains voltage
    - Current power draw
    - Current power usage
    - Total energy consumption (in kilowatt-hours)

1. Apply the new configuration by restarting Moonraker

   ```bash {title="Restarting the Mooraker service"}
   sudo systemctl restart moonraker
   ```

1. Confirm Data Exchange

   To ensure the successful publication of measurements from the power meter and Moonraker's ability to process them, navigate to the Mainsail Web UI for your printer.

   If the integration is functioning correctly, you should observe four new measurements from your sensor in the 'Miscellaneous Card' on the dashboard, as depicted in the screenshot below:

   ![Mainsail Sensor Data Display](images/guides/energy-usage-monitoring/mainsail-sensor-data.png)

   This verification step confirms the accurate exchange of data between the power meter and Moonraker, enabling real-time monitoring and analysis of energy consumption.

   {{< callout context="caution" title="Troubleshooting Data Exchange Issues" icon="outline/alert-triangle" >}}
   If the expected data fails to appear in the Web UI, some troubleshooting will need to be performed.

   {{< details "Troubleshooting steps" >}}
   1. Review the `moonraker.log` file for any configuration errors related to MQTT integration.
   2. Confirm that the power meter is publishing data in the expected format. Utilize a tool like [MQTT Explorer](http://mqtt-explorer.com/) to connect to the MQTT server and verify real-time updates and message content.
   {{< /details >}}
   {{< /callout >}}

### Historical Data

Moonraker allows tracking auxillary sensor data in the job history. To facilitate persisting this data additional history fields need to be configured for the sensor.

1. Execute the following command to access and modify the Moonraker configuration file

   ```bash {title="Editing the Moonraker configuration file"}
   sudo nano ~/printer_data/config/moonraker.conf
   ```

2. Enhance sensor definition with history fields

   Append the following configuration lines to the previously defined sensor:

   ```ini {title="moonraker.conf"}
   history_field_energy_consumption:
     parameter=energy
     desc=Energy consumption
     strategy=delta
     units=kWh
     init_tracker=true
     precision=6
     exclude_paused=false
     report_total=true
     report_maximum=true
   history_field_average_power:
     parameter=power
     desc=Average power draw
     strategy=average
     units=W
     report_total=false
     report_maximum=true
   history_field_max_power:
     parameter=power
     desc=Maximum power draw
     strategy=maximum
     units=W
     init_tracker=true
     report_total=false
     report_maximum=false
   history_field_average_current:
     parameter=current
     desc=Average current draw
     strategy=average
     units=A
     report_total=false
     report_maximum=true
   history_field_max_current:
     parameter=current
     desc=Maximum current draw
     strategy=maximum
     units=A
     init_tracker=true
     report_total=false
     report_maximum=false
   ```

   This modification adds fields for current draw, power usage, and energy consumption, which will be recorded in the job history upon completion of a print job.

3. Apply the new configuration by restarting Moonraker

   ```bash {title="Restarting the Mooraker service"}
   sudo systemctl restart moonraker
   ```

4. Verify data tracking in Mainsail

   To confirm the successful integration of power meter measurements and Moonraker's job history, access the Mainsail Web UI for your printer. If the configuration has been completed correctly, you should see additional columns in the Job History section, as depicted in the screenshot below:

   ![Mainsail Job History Display](images/guides/energy-usage-monitoring/mainsail-job-history.png)

   {{< callout context="note" title="Note" icon="outline/info-circle" >}}
   The newly added fields will be blank for existing entries in the job history. As new print jobs are completed, these fields will be populated with the relevant data.
   {{< /callout >}}

## Further Reading

- Moonraker [sensor configuration](https://moonraker.readthedocs.io/en/latest/configuration/#sensor) documentation
- Shelly [web interface guide](https://kb.shelly.cloud/knowledge-base/shelly-pro-1pm-web-interface-guide)
