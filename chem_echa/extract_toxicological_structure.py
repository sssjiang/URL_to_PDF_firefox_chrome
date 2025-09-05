#!/usr/bin/env python3
"""
Extracts toxicological information links from ECHA dossier HTML and converts to structured JSON.
"""

import re
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional


class ToxicologicalExtractor:
    def __init__(self, html_file_path: str = None, html_content: str = None):
        """Initialize with HTML file path or HTML content."""
        self.html_file_path = html_file_path
        self.html_content = html_content
        self.soup = None
        self.load_html()
    
    def load_html(self):
        """Load and parse HTML from file or content."""
        try:
            if self.html_content:
                # 直接使用提供的HTML内容
                content = self.html_content
            elif self.html_file_path:
                # 从文件读取HTML内容
                with open(self.html_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                raise ValueError("必须提供html_file_path或html_content参数")
            
            self.soup = BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"Error loading HTML: {e}")
            raise
    
    def extract_toxicological_structure(self) -> Dict[str, Any]:
        """
        Extract the complete toxicological information structure from HTML.
        Returns a nested dictionary representing the hierarchical structure.
        """
        # Find the main toxicological information section
        tox_section = self.soup.find('div', {'id': 'id_7_Toxicologicalinformation'})
        if not tox_section:
            print("Toxicological information section not found!")
            return {}
        
        result = {}
        
        # Extract the main section title
        main_title = "7 Toxicological information"
        result[main_title] = self._extract_section_content(tox_section)
        
        return result
    
    def _extract_section_content(self, section_element) -> Dict[str, Any]:
        """
        Recursively extract content from a section element.
        """
        content = {}
        
        # Find all direct child list items that represent subsections
        direct_children = section_element.find('ul')
        if not direct_children:
            return content
            
        # Find all li elements that are direct children
        li_elements = direct_children.find_all('li', recursive=False)
        
        for li in li_elements:
            # Check if this li contains a subsection
            subsection_div = li.find('div', class_='das-nav-topsection')
            if subsection_div:
                # Extract section title
                button = subsection_div.find('button')
                if button:
                    section_title = button.get_text(strip=True)
                    
                    # Find the corresponding collapse div for this subsection
                    target_id = button.get('data-toc-target', '').lstrip('#')
                    if target_id:
                        collapse_div = li.find('div', {'id': target_id})
                        if collapse_div:
                            # Recursively extract content from this subsection
                            subsection_content = self._extract_section_content(collapse_div)
                            content[section_title] = subsection_content
        
        # After processing all subsections, look for direct links at this level
        # Find das-leaf_parent elements that contain direct links
        leaf_parents = section_element.find_all('li', class_='das-leaf_parent')
        for leaf_parent in leaf_parents:
            # Make sure this leaf_parent is at the current level, not in a subsection
            if self._is_direct_child_leaf(leaf_parent, section_element):
                link_data = self._extract_link_from_li(leaf_parent)
                if link_data:
                    content.update(link_data)
        
        return content
    
    def _is_direct_child_leaf(self, leaf_element, section_element) -> bool:
        """
        Check if a leaf element is a direct child of the section, not nested in subsections.
        """
        # Walk up the DOM to see if there's a subsection div between this leaf and the section
        current = leaf_element.parent
        while current and current != section_element:
            # If we encounter a collapse div with an ID that starts with 'id_', it's a subsection
            if (current.name == 'div' and 
                current.get('class') and 'collapse' in current.get('class') and
                current.get('id') and current.get('id').startswith('id_') and
                current.get('id') != section_element.get('id')):
                return False
            current = current.parent
        return True
    
    def _extract_direct_links(self, section_element) -> Dict[str, str]:
        """
        Extract direct links from a section that don't have subsections.
        """
        links = {}
        
        # Find all das-leaf elements (direct links)
        leaf_elements = section_element.find_all('a', class_=lambda x: x and 'das-leaf' in x and 'das-docid' in x)
        
        for leaf in leaf_elements:
            # Extract the href (document ID)
            href = leaf.get('href', '')
            
            # Extract the link text/title
            span = leaf.find('span', class_='das-has-tooltip')
            if span:
                link_title = span.get_text(strip=True)
                if link_title and href:
                    links[link_title] = href
        
        return links
    
    def _extract_link_from_li(self, li_element) -> Optional[Dict[str, str]]:
        """
        Extract link information from a list item element.
        """
        # Look for das-leaf link
        leaf_link = li_element.find('a', class_=lambda x: x and 'das-leaf' in x and 'das-docid' in x)
        
        if leaf_link:
            href = leaf_link.get('href', '')
            span = leaf_link.find('span', class_='das-has-tooltip')
            if span and href:
                link_title = span.get_text(strip=True)
                return {link_title: href}
        
        return None
    
    def save_to_json(self, output_file: str, data: Dict[str, Any]):
        """Save extracted data to JSON file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {output_file}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")
    
    def print_structure(self, data: Dict[str, Any], indent: int = 0):
        """Print the structure in a readable format."""
        for key, value in data.items():
            print("  " * indent + f"- {key}")
            if isinstance(value, dict):
                if value:  # If not empty
                    self.print_structure(value, indent + 1)
                else:
                    print("  " * (indent + 1) + "(empty)")
            else:
                print("  " * (indent + 1) + f"-> {value}")


def main():
    """Main function to run the extraction."""
    # Input HTML file path
    html_file = "dosser_detail.html"
    output_file = "toxicological_structure.json"
    
    try:
        # Create extractor instance
        extractor = ToxicologicalExtractor(html_file)
        
        # Extract the structure
        print("Extracting toxicological information structure...")
        structure = extractor.extract_toxicological_structure()
        
        if structure:
            # Print structure
            print("\nExtracted Structure:")
            extractor.print_structure(structure)
            
            # Save to JSON
            extractor.save_to_json(output_file, structure)
            
            print(f"\nExtraction completed successfully!")
            print(f"Total sections found: {len(structure)}")
        else:
            print("No toxicological information found!")
            
    except Exception as e:
        print(f"Error during extraction: {e}")


if __name__ == "__main__":
    main()
