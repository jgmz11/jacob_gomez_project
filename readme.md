# COVID-19 Case Visualizion - Jacob Gomez Rubio
## Overview
This project attempts to load, process, and visualize data involving COVID-19 cases. The data contains data on confirmed cases, deaths, and similar variables.

## Setup the environment
To setup, `run.sh` has been configured to install dependendencies (using the Anaconda package manager as a preqrequisite). 
> Note: If environment issues arise or if Anaconda is not installed on your machine, use `pip install -r requirements.txt` to import the necessary project dependencies.

## Running the code
Executable code sits in `covid.py`. The shell script `run.sh` will also execute `covid.py` after the necessary packages have been installed. Once the code has executed, a local web server will be started using the Flask and Dash frameworks. The server is accessible through port 8050, or by typing `localhost:8050` in your web browser.

## Data Flow
The COVID-19 case data goes through a series of processes before reaching final visualization.
1. We check for a valid URL, and load data from there, asserting that the data pulled is not empty or corrupted.
2. Case data is explored and cleaned, using QA/QC to ensure:
    - null values are filled
    - empty/data-lacking rows are dropped
    - there is data type uniformity for each column
    - columns are properly casted depending on their purpose, e.g. `FIPS` follows a 5-digit code which signifies specific county ID, and lat/long columns are casted to float64 for precision.
3. FIPS data and lat/long data were joined to case data using a second data source.

## Visualization
After final data processing, graphs are created using Plotly and Dash frameworks.

- **There are 3 graphs -- a bubble map, a choropleth map, and a bar chart**
    - A bubble map allows us to view data in multiple dimensions, both confirmed cases as well as deaths. The size of the bubble indicates case count, and deaths are indicated by the bubble color.
    - A choropleth map allows us to view data at a more granular level than the bubble. We can see cases by exact county boundaries and impact colors, which could help drive insight to which communities are most affected by the virus.
    - The bar chart allows us to understand the top 10 counties by case counts.

## Conclusion
This project should be very easy to run. If there are any issues with execution, please flag to me. Thank you for the opportunity so far. Looking forward to next steps.