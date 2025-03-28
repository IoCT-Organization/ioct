# IoCT Project

## About the Invention

The Internet of Carbon Things (IoCT) is an innovative framework designed to monitor and mitigate carbon emissions across multiple levels—device, edge, and cloud. This project integrates sensor data collection (device level), local processing and decision-making (edge level), and centralized analytics and visualization (cloud level) to provide a comprehensive solution for emissions management. By leveraging IoT technologies, IoCT aims to enhance environmental sustainability through real-time monitoring and actionable insights.

## Cloning the Repository

To get started with the IoCT project, clone the complete repository from GitHub using SSH:

```bash
git clone git@github.com:IoCT-Organization/ioct.git
cd ioct
```

## Prerequisites

- **Git**: Ensure Git is installed (`git --version` to check).
- **SSH Key**: Configure an SSH key with your GitHub account to enable secure cloning and pushing.  
  Refer to GitHub’s guide: [Connecting to GitHub with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- **Python 3.x**: Required for running and developing edge (`emissions_edge/`) and cloud (`emissions_cloud/`) applications.
- **C Build Tools (for device-level development)**: Install a C compiler such as `gcc`, and SDK-specific tools like the Nordic nRF5 SDK (required for building and flashing applications in `nrc7292_sdk/`).
- **Python Dependencies**: Additional required packages can be installed via `pip` after cloning the repository (see Edge/Cloud setup sections below).

## Repository Structure

The cloned repository contains:

- `nrc7292_sdk/`: Device-level code and SDK, including the new `sample_ioct_client` application.
- `emissions_edge/`: Edge-level processing application.
- `emissions_cloud/`: Cloud-level analytics and dashboard.

## Device Level: Modifying and Building the Development Application

The device-level application resides in `nrc7292_sdk/`, interfacing with hardware (e.g., NRF7292 sensors) to collect emissions data. We’ve implemented a new application, `sample_ioct_client`, based on the `sample_tcp_client` example, customized for IoCT’s carbon emissions use case.

### Steps

#### Navigate to the Directory

```bash
cd nrc7292_sdk/package/standalone/sdk/apps/
```

#### Create the New Application

Copy the `sample_tcp_client` example to create `sample_ioct_client`:

```bash
cp -r sample_tcp_client sample_ioct_client
cd sample_ioct_client
```

_(More steps to follow for file edits, compilation, and flashing...)_

### File Modifications

Once inside the `sample_ioct_client/` directory, follow these steps:

---

#### 1. Rename the Main File

Rename the example source file:

```bash
mv sample_tcp_client.c sample_ioct_client.c
```

---

#### 2. Modify the Makefile

Open `Makefile` and update the following lines:

```makefile
TARGET = sample_ioct_client
SRCS = sample_ioct_client.c
```

Ensure the rest of the Makefile uses these variables for compilation and linking.

---

#### 3. Edit `sample_ioct_client.c`

Replace the logic to collect and send emissions data (CO₂, CH₄, N₂O). Here’s a pseudocode snippet to guide the update:

```c
struct EmissionData {
    float co2;
    float ch4;
    float n2o;
};

// Format and send as JSON string
sprintf(json, "{\"CO2\": %.2f, \"CH4\": %.2f, \"N2O\": %.2f}", data.co2, data.ch4, data.n2o);
send(socket_fd, json, strlen(json), 0);
```

---

### Build the Application

Make sure you are inside the `sample_ioct_client/` directory:

```bash
make
```

This compiles your application using the SDK's build system.

---

### Flash the Firmware to the Device

Use Nordic’s `nrfjprog` to flash your compiled binary (e.g., `output.hex`):

```bash
nrfjprog --program build/output.hex --chiperase
nrfjprog --reset
```

Make sure the device is connected and JLink is recognized.

---

### Test via Serial Console

Check if the device is running and emitting expected output:

```bash
screen /dev/ttyUSB0 115200
```

Use `Ctrl+A` then `\` to exit `screen`.

---

✅ At this point, your device should be collecting carbon emissions data and preparing it for edge-level transmission.

## Edge Level: Modifying and Building the Development Application

The edge-level application in `emissions_edge/` processes data locally and communicates with the cloud.

### Steps

**Navigate to the Directory:**

```bash
cd emissions_edge
```

**Modify the Code:**

Open `edge.py` (or equivalent) in an editor.

Example modification: Adjust MQTT topic:

```python
mqtt_topic = "emissions/data/edge1"  # Change to a unique identifier
```

**Install Dependencies:**

Ensure Python and required libraries are installed:

```bash
pip3 install paho-mqtt pandas
```

**Build/Run the Application:**

Run directly:

```bash
python3 edge.py
```

Ensure MQTT broker (e.g., `broker.hivemq.com`) is accessible.

**Test:**

Check console logs:

```text
Processed data: CO2e=510.94 kg at 2025-03-28T<time>
```

---

## Cloud Level: Modifying and Building the Development Application

The cloud-level application in `emissions_cloud/` provides analytics and a web dashboard.

### Steps

**Navigate to the Directory:**

```bash
cd emissions_cloud
```

**Modify the Code:**

Open `cloud.py` in an editor.

Example modification: Change plot color in `visualize_cloud_data()`:

```python
plt.plot(hourly.index, hourly["CO2e"], marker='o', color='#FF5733', label='CO2e')  # Changed to orange
```

**Install Dependencies:**

Install Python packages:

```bash
pip3 install flask pandas matplotlib paho-mqtt sqlite3
```

**Build/Run the Application:**

Start the Flask server:

```bash
python3 cloud.py
```

Access the dashboard at [http://localhost:5002](http://localhost:5002).

**Test:**

Verify plots and recommendations in the browser.

Check console:

```text
Simulated data: CO2e=1133.6 kg at 2025-03-28T<time>
```

---

## Additional Notes

### Directory Structure:

```text
ioct/
├── README.md
├── nrc7292_sdk/    # Device-level code with sample_ioct_client
├── emissions_edge/ # Edge-level code
└── emissions_cloud/ # Cloud-level code
```

### Troubleshooting:

- Ensure ports (e.g., 5002 for cloud) are free.
- Check SSH authentication if cloning fails (`ssh -T git@github.com`).

### Future Enhancements:

- Integrate real MQTT instead of simulation.
- Expand device support beyond NRF7292.
