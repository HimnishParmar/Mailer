# Mailer Project


## Overview

The Mailer project is a campaign management system built using Django, Tkinter, SQLite3, BeautifulSoup, and GrapesJS. This tool allows users to create and manage email campaigns efficiently. The project provides a user-friendly interface to handle various aspects of email marketing/phishing.


## Features

- **Campaign Management**: Create, modify, and manage email campaigns effortlessly.
- **User Interface**: A simple and intuitive interface powered by Tkinter for easy navigation.
- **Database**: Utilizes SQLite3 for storing campaign data securely and efficiently.
- **Web Scraping**: Leverages BeautifulSoup for scraping data as needed.
- **Email Template Editor**: Integrates GrapesJS for designing email templates visually.
- **Custom Domain (Future Scope)**: In the future, the project will allow tracking of links with custom domain names instead of the current same-server setup.
- **Standalone Website Templates (Future Scope)**: Users will be able to choose from multiple phishing templates or scrape live websites to use as templates.
- **Multi-Page Web Scraper (Future Scope)**: Future versions will allow users to scrape multiple connected web pages and interact with forms or links on the recipient site, while keeping the site running locally or on the user's server.
  

## Getting Started

To get started with the Mailer project, follow these instructions to download and run the application.

### Prerequisites

- Python >3.11.x
- Pip (Python package installer)

### Installation

1. **Clone the Repository**:

   You can either download the project as a ZIP file from GitHub or clone the repository using the following command
   ( If you don't have Git installed : from https://git-scm.com/downloads you can install it ):

   ```bash
   git clone https://github.com/HimnishParmar/Mailer.git
   ```

3. **Navigate to the Project Directory**:

   Change to the project directory:

   ```bash
   cd Mailer
   ```

4. **Run the Installer**:

   For **Windows**, execute the `Mailer.bat` file to start the application.

   For **Linux/MacOS**, execute the `Mailer.sh` file to start the application.

### Running the Application

- **Windows**: Double-click on `Mailer.bat` to launch the application.
- **Linux/MacOS**: Open a terminal and run the following command:

  ```bash
  bash Mailer.sh
  ```

### Usage

Once the application is running, you will be presented with the main interface. You can start creating and managing your email campaigns through the user-friendly GUI.


## API Services Used

This project utilizes the following API services to gather information about IP addresses:

- **Shodan**: A search engine for Internet-connected devices that provides data about vulnerabilities and configurations.
- **IPinfo**: A service that provides detailed information about IP addresses, including location, organization, and other relevant metadata.
- **IP-API**: A simple API for geolocation of IP addresses, offering information such as latitude, longitude, and city.
- **Ngrok**: A tool that creates secure tunnels to your localhost, allowing you to expose a local server to the internet. This is particularly useful for testing webhooks, API integrations, or sharing your work with others without deploying it to a public server.


## Required API Keys
To use the Mailer project effectively, you will need to obtain the following API keys and provide them in the settings panel of the application:

1. **Shodan API Key**: 
   - Sign up at [Shodan](https://account.shodan.io/register) and obtain your API key from your account settings. 
   - Enter your Shodan API key in the settings panel of the tool to enable functionality related to Shodan.

2. **Ngrok Auth Key**: 
   - Sign up at [Ngrok](https://dashboard.ngrok.com/signup) and get your auth token from the Ngrok dashboard.
   - Provide your Ngrok auth token in the settings panel to allow the application to create secure tunnels to your localhost.

### Setting Up API Keys
Once you have obtained your API keys, follow these steps:

- Open the Mailer application.
- Navigate to the settings panel.
- Enter your Shodan API key and Ngrok auth token in their respective fields.
- Save the settings to enable API functionality.

These keys are essential for the full operation of the Mailer project, allowing you to gather information about IP addresses and use Ngrok for tunneling.


## Future Scope

- **Standalone Servers**: Moving tracking links and campaigns to work across standalone servers and custom domains.
- **Multiple Phishing Templates**: Adding multiple website and email templates that users can select for their campaigns.
- **Advanced Web Scraper**: Enhance web scraping functionality to allow multi-page scraping, enabling users to interact with the original site through forms and links within their environment.
- **URL Crawling**: Implement URL crawling for dynamic content gathering and full-site scraping.
- **Legitimate Site Replication**: Automatically scrape and modify sites to make them look like legitimate sites for phishing simulations.


## Future Features

- **Advanced IP Geolocation**: Integration of additional IP tracking services for more precise geolocation and device data.
- **Standalone Server**: Tracking on custom domains with independent servers.
- **Email Phishing Templates**: Pre-designed and ready-to-use phishing templates for a variety of scenarios.
- **Multi-Page Scraping**: Full website scraping capabilities with form interaction, allowing users to simulate real websites locally.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Contributing

Contributions are welcome! If you have suggestions for improvements or bug fixes, please submit a pull request.


## Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework used for building the application.
- [Tkinter](https://wiki.python.org/moin/TkInter) - For the GUI.
- [CTkinter](https://customtkinter.tomschimansky.com/) - For the GUI.
- [SQLite3](https://www.sqlite.org/index.html) - For the database.
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - For web scraping.
- [GrapesJS](https://grapesjs.com/) - For the email template editor.
