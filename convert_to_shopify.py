import csv
import re
import os

def clean_html(text):
    if not text:
        return ""
    # Remove WordPress blocks comments
    text = re.sub(r'<!-- /?wp:.*? -->', '', text)
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Remove HTML but keep some basic tags
    # or just keep all and Shopify will render it
    return text.strip()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

input_file = '/Users/rupeshsingh/Downloads/kotabook.com/wc-product-export-2-3-2026-1772392873414.csv'
output_file = '/Users/rupeshsingh/Downloads/kotabook.com/shopify_import_kotacart.csv'

shopify_headers = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags", "Published",
    "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value", "Option3 Name", "Option3 Value",
    "Variant SKU", "Variant Grams", "Variant Inventory Tracker", "Variant Inventory Qty",
    "Variant Inventory Policy", "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
    "Variant Requires Shipping", "Variant Taxable", "Variant Barcode", "Image Src",
    "Image Position", "Image Alt Text", "Gift Card", "SEO Title", "SEO Description",
    "Google Shopping / Google Product Category", "Google Shopping / Gender", "Google Shopping / Age Group",
    "Google Shopping / MPN", "Google Shopping / Condition", "Google Shopping / Custom Product",
    "Google Shopping / Custom Label 0", "Google Shopping / Custom Label 1", "Google Shopping / Custom Label 2",
    "Google Shopping / Custom Label 3", "Google Shopping / Custom Label 4", "Variant Image",
    "Variant Weight Unit", "Variant Tax Code", "Cost per item", "Price / International",
    "Compare At Price / International", "Status"
]

with open(input_file, mode='r', encoding='utf-8-sig') as f: # Use utf-8-sig to handle BOM
    reader = csv.DictReader(f)
    rows = list(reader)

shopify_rows = []
parent_id_map = {}

# Pass 1: Handle parent products
for row in rows:
    p_type = row.get('Type', '').lower()
    if p_type in ['simple', 'variable']:
        handle = slugify(row['Name'])
        parent_id_map[row['ID']] = {
            'Handle': handle,
            'Title': row['Name'],
            'Body': f"{clean_html(row.get('Short description', ''))}<br><br>{clean_html(row.get('Description', ''))}".strip(),
            'Tags': (row.get('Tags', '') + ", " + row.get('Categories', '')).strip(", "),
            'Published': "TRUE" if row.get('Published') == '1' else "FALSE",
            'Status': "active" if row.get('Published') == '1' else "archived"
        }

# Pass 2: Generation
for row in rows:
    p_id = row['ID']
    p_type = row.get('Type', '').lower()
    
    if p_type == 'variation':
        parent_id = row.get('Parent', '')
        p_info = parent_id_map.get(parent_id, {})
        handle = p_info.get('Handle', f"product-{parent_id}")
        title = "" # Sub-variations don't need title row
        body = ""
        tags = ""
        published = p_info.get('Published', 'TRUE')
        status = p_info.get('Status', 'active')
    else:
        p_info = parent_id_map.get(p_id, {})
        handle = p_info.get('Handle', slugify(row['Name']))
        title = p_info.get('Title', row['Name'])
        body = p_info.get('Body', "")
        tags = p_info.get('Tags', "")
        published = p_info.get('Published', 'TRUE')
        status = p_info.get('Status', 'active')

    # Images
    image_paths = [img.strip() for img in row.get('Images', '').split(',') if img.strip()]
    
    # Options
    # WooCommerce Attribute 1 value(s) can be "2021, 2022" for variable, 
    # but for a variation, it's just one value "2021".
    opt1_name = row.get('Attribute 1 name', '')
    opt1_val = row.get('Attribute 1 value(s)', '')
    opt2_name = row.get('Attribute 2 name', '')
    opt2_val = row.get('Attribute 2 value(s)', '')

    # Shopify: first row with handle defines the product options.
    # Simple products: Option1 Name = Title, Option1 Value = Default Title.
    if p_type == 'simple':
        opt1_name = "Title"
        opt1_val = "Default Title"
    
    price = row.get('Sale price') or row.get('Regular price')
    compare_at = row.get('Regular price') if row.get('Sale price') else ""
    
    s_row = {h: "" for h in shopify_headers}
    s_row["Handle"] = handle
    s_row["Title"] = title
    s_row["Body (HTML)"] = body
    s_row["Vendor"] = "Kotacart"
    s_row["Type"] = "Study Material"
    s_row["Tags"] = tags
    s_row["Published"] = published
    s_row["Option1 Name"] = opt1_name
    s_row["Option1 Value"] = opt1_val
    s_row["Option2 Name"] = opt2_name
    s_row["Option2 Value"] = opt2_val
    s_row["Variant SKU"] = row.get('SKU', '')
    s_row["Variant Price"] = price
    s_row["Variant Compare At Price"] = compare_at
    s_row["Variant Inventory Tracker"] = "shopify"
    s_row["Variant Inventory Qty"] = row.get('Stock', '10') if row.get('In stock?') == '1' else '0'
    s_row["Variant Inventory Policy"] = "deny"
    s_row["Variant Fulfillment Service"] = "manual"
    s_row["Variant Requires Shipping"] = "TRUE"
    s_row["Variant Taxable"] = "TRUE"
    s_row["Image Src"] = image_paths[0] if image_paths else ""
    s_row["Image Position"] = "1" if image_paths else ""
    s_row["Status"] = status
    
    shopify_rows.append(s_row)
    
    # Add extra rows for additional images
    if len(image_paths) > 1:
        for i, img_src in enumerate(image_paths[1:], start=2):
            img_row = {h: "" for h in shopify_headers}
            img_row["Handle"] = handle
            img_row["Image Src"] = img_src
            img_row["Image Position"] = str(i)
            shopify_rows.append(img_row)

with open(output_file, mode='w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=shopify_headers)
    writer.writeheader()
    writer.writerows(shopify_rows)

print(f"Success: Shopify import file created at {output_file}")
