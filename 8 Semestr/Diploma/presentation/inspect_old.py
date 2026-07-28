from pptx import Presentation
from lxml import etree
import re

prs = Presentation(r'D:\Programming\Projects\8 Semestr\Diploma\presentation\Example.pptx')

# Check slide master for sRGB hex colors
s2 = prs.slides[1]
master = s2.slide_layout.slide_master
bg_xml = etree.tostring(master._element, pretty_print=True).decode()
pattern = r'srgbClr val="([0-9A-Fa-f]{6})"'
srgb = re.findall(pattern, bg_xml)
print('sRGB colors in master:', srgb[:20])

# Check slide 2 layout xml for header bar
layout = s2.slide_layout
lxml = etree.tostring(layout._element, pretty_print=True).decode()
srgb2 = re.findall(pattern, lxml)
print('sRGB in layout:', srgb2[:10])

# Check slide 2 own xml
s2xml = etree.tostring(s2._element, pretty_print=True).decode()
srgb3 = re.findall(pattern, s2xml)
print('sRGB in slide 2:', srgb3[:10])

# Print all layouts
print('\nLayouts:')
for i, layout in enumerate(master.slide_layouts):
    print(f'  {i}: {layout.name}')
