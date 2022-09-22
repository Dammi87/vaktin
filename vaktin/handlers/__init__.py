import pandas as pd
import json
import math
import os
import locale
from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
from ..lib.ops import get_dir
from ..lib import Borg

# Set locale
locale.setlocale(locale.LC_ALL, '' )


def get_currency_string(price):
    if price == 'nan' or math.isnan(price):
        return 'N/A'
    return locale.currency(int(price), grouping=True )


def calculate_total_price(price_strings):
    total_price = 0
    for price in price_strings:
        if price == 'N/A':
            continue

        if isinstance(price, int):
            total_price += price
            continue

        if isinstance(price, str):
            try:
                total_price += int(price)
            except:
                total_price += int(''.join(price.split(' ')[0].split('.')))
            continue

    return get_currency_string(total_price)


def get_config():
    cfg_path = os.path.join(
        get_dir(__file__),
        'cfg.json'
    )
    with open(cfg_path, 'r') as f:
        return json.load(f)


def get_soup(url):
    source = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source, 'html.parser')
    return soup


def get_tables(soup, table_idx, sellers, part):
    tables = soup.find_all('table', attrs={'class':'prices'})
    if table_idx is None:
        table_idx = range(len(tables))

    order = ['Name'] + sellers
    res_dict = {name: [] for name in order + ['Brand', 'Part']}
    for idx in table_idx:
        table = tables[idx]
        table_rows = table.find_all('tr')
        brand_title = table.find_all('th', attrs={'class': 'brandTitle'})[0].getText()

        for tr in table_rows:
            td = tr.find_all('td')
            row = [item.text.strip() for item in td]
            if row:
                for idx, key in enumerate(order):
                    value = row[idx]
                    if idx > 0:
                        if row[idx] == '':
                            value = float('nan')
                        else:
                            value = int(row[idx].replace('.', ''))

                    res_dict[key].append(value)
                res_dict['Brand'].append(brand_title)
                res_dict['Part'].append(part)

    df = pd.DataFrame(res_dict)
    df['Cheapest'] = df.loc[:, sellers].min(axis=1)
    # Drop any that have all empty
    df = df.dropna(subset=sellers, how='all')
    # Drop any that have the same brand and name
    return df.drop_duplicates(subset=['Brand', 'Name'])


class Vaktin(Borg):
    def __init__(self, dfs={}):
        cfg = get_config()
        self._url_dict = cfg['URL_DICT']
        self._base_url = cfg['BASE_URL']
        self._sellers = cfg['SELLER_ORDER']
        self._parts = list(cfg['URL_DICT'].keys())
        self.dfs = dfs

        self._selected_component = None
        self._vendor_type = None
        self.components_per_part = None
        self._merged_tables = None

    def get_parts(self):
        return self._parts
    
    def get_merged_tables(self):
        if self._merged_tables is None:
            df = []
            for part in self.get_parts():
                df.append(self.get_dataframe(part))
            self._merged_tables = pd.concat(df)
        return self._merged_tables

    def get_available_parts(self):
        return self._parts
    
    def _init_component_selection(self):
        if self._selected_component is None:
            self._selected_component = {}
            for part in self.get_available_parts():
                brand = self.get_brands(part)[0]
                self._selected_component[part] = (brand, self.get_components(part, brand)[0])

    def get_selected_component(self, part_name):
        self._init_component_selection()
        return self._selected_component[part_name]

    def set_selected_component(self, part_name, brand_name, component_name):
        print('Changing selected component for {} -> {}'.format(part_name, component_name))
        self._init_component_selection()
        self._selected_component[part_name] = (brand_name, component_name)

    def get_build(self):
        dfs = []
        self._init_component_selection()
        for part in self._selected_component:
            brand, component = self._selected_component[part]
            df = self.get_filter_frame(part, part_name=part, brand_name=brand, component_name=component)
            dfs.append(df)
        df = pd.concat(dfs)
        vendor = self.get_vendor()

        df = df.rename(
                columns={
                    'Name': 'Component',
                    vendor: 'Price',
                }
        )[['Part', 'Brand', 'Component', 'Price']]
        df['Vendor'] = vendor

        if vendor == 'Cheapest':
            vendors = []
            for part in self._selected_component:
                brand, component = self._selected_component[part]
                vendors.append(self.get_cheapest_seller(part, brand, component))
            df['Vendor'] = vendors
        
        # Now change formats
        df['Price'] = [get_currency_string(price) for price in df.Price.tolist()]
        total_price = calculate_total_price(df.Price.tolist())
        total_price = df.Price.tolist() + [total_price]
        df = df.append(pd.Series(), ignore_index=True)
        df['Price'] = total_price

        return df


    def get_vendors(self):
        return self._sellers + ['Cheapest']
    
    def get_vendor(self):
        if self._vendor_type is None:
            self.set_vendor(self.get_vendors()[0])
        return self._vendor_type

    def set_vendor(self, vendor_name):
        print("Setting vendor: {}".format(vendor_name))
        self._vendor_type = vendor_name

    def get_cheapest_seller(self, part_name, brand_name, component_name):
        df = self.get_filter_frame(part_name, component_name=component_name, brand_name=brand_name)
        return df[self._sellers].T.idxmin().values[0]

    def get_components(self, part_name, brand_name):
        df = self.get_filter_frame(part_name, brand_name=brand_name)
        return df.Name.tolist()

    def get_brands(self, part_name):
        return self.get_dataframe(part_name).Brand.unique().tolist()
    
    def get_filter_frame(self, part, part_name=None, brand_name=None, component_name=None):
        df = self.get_dataframe(part)
        if part_name is not None:
            df = df[df.Part == part_name]
        if brand_name is not None:
            df = df[df.Brand == brand_name]
        if component_name is not None:
            df = df[df.Name == component_name]
        return df

    def fetch_dataframes(self):
        for part in self._url_dict:
            url_dict = self._url_dict[part]
            url = self._base_url.format(url_dict['url'])
            soup = get_soup(url)
            df = get_tables(soup, url_dict['tables'], self._sellers, part)
            self.dfs[part] = df

    def get_dataframe(self, part_name):
        if not self.dfs:
            self.fetch_dataframes()

        return self.dfs[part_name]
