import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

def scrape_screener(company_input):
    consolidated_url = f"https://www.screener.in/company/{company_input}/consolidated/"
    standalone_url = f"https://www.screener.in/company/{company_input}/"
    
    # First scraping data from the consolidated view 
    current_pe, roce = scrape_data_from_url(consolidated_url)
    
    # If data is not found in the consolidated view, it will be scraping from the standalone view
    if current_pe is None or roce is None:
        current_pe, roce = scrape_data_from_url(standalone_url)

    return current_pe, roce

def scrape_data_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        company_ratios_div = soup.find_all('div', class_='company-ratios')

        current_pe = None
        roce = None

        for div in company_ratios_div:
            li_elements = div.find_all('li', class_='flex flex-space-between')

            for li in li_elements:
                name_span = li.find('span', class_='name')
                value_span = li.find('span', class_='nowrap value')

                if name_span.text.strip() == 'Stock P/E':
                    current_pe_text = value_span.text.strip()
                    if current_pe_text:
                        current_pe = float(current_pe_text)
                        st.write('Current P/E:',current_pe)

        section = soup.find("section", id="ratios")                                     
        if section:
            table = section.find("table")                                              
            if table:
                rows = table.find_all("tr")                                             
                header_row = rows[0]                                                    
                headers = [cell.text.strip() for cell in header_row.find_all(["th", "td"])]
                year_column_index = None
                for index, header in enumerate(headers):
                    if "2019" in header:
                        year_column_index = index
                        break

                if year_column_index is not None:
                    for row in rows:
                        cells = row.find_all(["th", "td"])
                        if cells and cells[0].text.strip() == "ROCE %":
                            roce_text = cells[year_column_index].text.strip()
                            roce_text = roce_text.replace('%', '')  # Remove percentage sign
                            if roce_text:
                                roce = float(roce_text)
                                break

        return current_pe, roce
    
    return None, None

st.title("Stock Data Dashboard")
company_input = st.text_input('Enter the company symbol (default is NESTLEIND):', 'NESTLEIND')

current_pe, roce = scrape_screener(company_input)
if roce:
    st.write("5-yr median pre-tax RoCE:", roce)
else:
    st.write("ROCE% not found for the specified symbol.")

# For Getting FY23_PE
        
def scrape_fy(company_input):
    consolidated_url = f"https://www.screener.in/company/{company_input}/consolidated/"
    standalone_url = f"https://www.screener.in/company/{company_input}/"
    
    # Try scraping data from the consolidated view first
    fy23_pe = scrape_fy_from_url(consolidated_url)
    
    # If data is not found in the consolidated view, try scraping from the standalone view
    if fy23_pe is None:
        fy23_pe = scrape_fy_from_url(standalone_url)

    return fy23_pe

def scrape_fy_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        market_cap = soup.find('span', class_='number').text.strip()
        
        section = soup.find("section", id="profit-loss")
        if section:
            table = section.find("table")
            if table:
                rows = table.find_all("tr")

                header_row = rows[0]
                headers = [cell.text.strip() for cell in header_row.find_all(["th", "td"])]
                year_column_index = None
                for index, header in enumerate(headers):
                    if "2022" in header:
                        year_column_index = index
                        break

                for row in rows:
                    cells = row.find_all(["th", "td"])
                    if cells and "Net Profit" in cells[0].text.strip():
                        if year_column_index is not None and len(cells) > year_column_index:
                            net_profit_data = cells[year_column_index].text.strip()
                            break

                if market_cap and net_profit_data:
                    fy23 = float(market_cap.replace(',', '')) / float(net_profit_data.replace(',', ''))
                    return fy23
                
    return None

fy23_pe = scrape_fy(company_input)
if fy23_pe:
    st.write(f"FY23 PE (Price-to-Earnings) ratio for {company_input}:", fy23_pe)
else:
    st.write("Unable to fetch data for FY23 PE calculation.")

# For getting Proft & Sales Table 

# Function to scrape sales and profit growth data from Screener.in

def scrape_screener_tables(company):
    consolidated_url = f"https://www.screener.in/company/{company}/consolidated/"
    standalone_url = f"https://www.screener.in/company/{company}/"
    
    # Try scraping data from the consolidated view first
    sales_data, profit_data = scrape_screener_tables_from_url(consolidated_url)
    
    # If data is not found in the consolidated view, try scraping from the standalone view
    if not sales_data or not profit_data:
        sales_data, profit_data = scrape_screener_tables_from_url(standalone_url)

    return sales_data, profit_data

def scrape_screener_tables_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        sales_data, profit_data = {}, {}
        
        tables = soup.find_all("table", class_="ranges-table")
        for table in tables:
            header_text = table.find("th").text.strip()
            if "Compounded Sales Growth" in header_text:
                sales_data = {row.find_all("td")[0].text.strip().replace(":", ""): float(row.find_all("td")[1].text.strip().replace("%", "")) for row in table.find_all("tr")[1:] if row.find_all("td")[1].text.strip().replace("%", "")}  # Check if growth value is available
            elif "Compounded Profit Growth" in header_text:
                profit_data = {row.find_all("td")[0].text.strip().replace(":", ""): float(row.find_all("td")[1].text.strip().replace("%", "")) for row in table.find_all("tr")[1:] if row.find_all("td")[1].text.strip().replace("%", "")}  # Check if growth value is available
                
        return sales_data, profit_data

    return None, None


sales_growth_data, profit_growth_data = scrape_screener_tables(company_input)

# Visualize sales growth data
if sales_growth_data:
    st.subheader("Sales Growth Data:")
    sales_df = pd.DataFrame(sales_growth_data.items(), columns=["Period", "Growth"])
    st.dataframe(sales_df)
else:
    st.write("Sales Growth data not found for the specified symbol.")

# Visualize profit growth data
if profit_growth_data:
    st.subheader("Profit Growth Data:")
    profit_df = pd.DataFrame(profit_growth_data.items(), columns=["Period", "Growth"])
    st.dataframe(profit_df)
else:
    st.write("Profit Growth data not found for the specified symbol.")

# For Calculating Intrinsic PE & degree of overvaluation
 
def calculate_intrinsic_pe(cost_of_capital, RoCE, high_growth_rate, high_growth_period, fade_period, terminal_growth_rate):
    intrinsic_PE = 0
    for i in range(high_growth_period + fade_period):
        if i < high_growth_period:
            growth_rate = high_growth_rate
        else:
            remaining_fade_periods = fade_period - (i - high_growth_period)
            growth_rate = high_growth_rate - (high_growth_rate - terminal_growth_rate) * (remaining_fade_periods / fade_period)
        intrinsic_PE += (1 + growth_rate) / (1 + cost_of_capital) ** (i + 1)
    intrinsic_PE /= RoCE - cost_of_capital
    return intrinsic_PE

def main():
    st.title("Valuing Consistent Compounders")
    
    #  Creating Sliders

    cost_of_capital_range = [8, 9, 10, 11, 12, 13, 14, 15, 16]
    roce_range = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    growth_high_period_range = [8, 10, 12, 14, 16, 18, 20]
    high_growth_period_range = [10, 12, 14, 16, 18, 20, 22, 24, 25]
    fade_period_range = [5, 10, 15, 20]
    terminal_growth_rate_range = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.5]  

    # Selecting Sliders 

    cost_of_capital = st.slider("Cost of Capital (%)", min_value=min(cost_of_capital_range), max_value=max(cost_of_capital_range), step=1, value=min(cost_of_capital_range))
    roce = st.slider("Return on Capital Employed (RoCE) (%)", min_value=min(roce_range), max_value=max(roce_range), step=10, value=min(roce_range))
    growth_high_period = st.slider("Growth during high growth period ($)", min_value=min(growth_high_period_range), max_value=max(growth_high_period_range), step=2, value=min(growth_high_period_range))
    high_growth_period = st.slider("High growth period (years)", min_value=min(high_growth_period_range), max_value=max(high_growth_period_range), step=2, value=min(high_growth_period_range))
    fade_period = st.slider("Fade period (years)", min_value=min(fade_period_range), max_value=max(fade_period_range), step=5, value=min(fade_period_range))
    terminal_growth_rate = st.slider("Terminal growth rate (%)", min_value=min(terminal_growth_rate_range), max_value=max(terminal_growth_rate_range), step=0.5, value=min(terminal_growth_rate_range))

    # TO Display the inputs

    #st.write("Cost of Capital:", cost_of_capital, "%")
    #st.write("RoCE:", roce, "%")
    #st.write("Growth during high growth period:", growth_high_period, "$")
    #st.write("High growth period:", high_growth_period, "years")
    #st.write("Fade period:", fade_period, "years")
    #st.write("Terminal growth rate:", terminal_growth_rate, "%")

    # Calculate intrinsic P/E

    intrinsic_PE = calculate_intrinsic_pe(cost_of_capital, roce, growth_high_period, high_growth_period, fade_period, terminal_growth_rate)
    
    # Fetch current P/E and FY23 P/E

    current_PE,_ = scrape_screener(company_input)
    FY23_PE = scrape_fy(company_input)

    # Calculate degree of overvaluation

    if current_PE and FY23_PE:
        if current_PE < FY23_PE:
            degree_of_overvaluation = (current_PE / intrinsic_PE) - 1
        else:
            degree_of_overvaluation = (FY23_PE / intrinsic_PE) - 1
        st.write("The Calculated Intrinsic P/E is:", intrinsic_PE)
        st.write("Degree of Overvaluation:", degree_of_overvaluation)
    else:
        st.write("Unable to fetch current P/E or FY23 P/E data.")

if __name__ == "__main__":
    main()
