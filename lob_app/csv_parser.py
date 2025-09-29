from __future__ import annotations

import pandas as pd
from typing import Dict, List, Optional, Any
import re


class CSVParser:
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.knowledge_base: Dict[str, Any] = {}
        self._parse_csv()
    
    def _parse_csv(self) -> None:
        """Parse the CSV file and create a structured knowledge base."""
        try:
            # Read CSV with proper handling of multiline content
            df = pd.read_csv(self.csv_file_path, encoding='utf-8')
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Process each row to extract issue types and resolutions
            for _, row in df.iterrows():
                self._process_row(row)
                
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            # Create fallback knowledge base
            self._create_fallback_kb()
    
    def _process_row(self, row: pd.Series) -> None:
        """Process a single row from the CSV."""
        nodes = str(row.get('Nodes', '')).strip()
        if not nodes or nodes == 'nan':
            return
            
        # Extract issue type from the first column
        issue_type = self._extract_issue_type(nodes)
        if not issue_type:
            return
            
        # Get VOC examples
        voc_examples = self._extract_voc_examples(str(row.get('Sub-type / VOC', '')))
        
        # Get resolutions for different tiers
        gold_resolution = str(row.get('Gold', '')).strip()
        silver_bronze_resolution = str(row.get('Silver & Bronze', '')).strip()
        new_iron_resolution = str(row.get('New & Iron', '')).strip()
        
        # Store in knowledge base
        if issue_type not in self.knowledge_base:
            self.knowledge_base[issue_type] = {
                'voc_examples': [],
                'resolutions': {
                    'gold': gold_resolution,
                    'silver_bronze': silver_bronze_resolution,
                    'new_iron': new_iron_resolution
                },
                'sop_details': nodes
            }
        
        # Add VOC examples
        self.knowledge_base[issue_type]['voc_examples'].extend(voc_examples)
    
    def _extract_issue_type(self, nodes_text: str) -> Optional[str]:
        """Extract the main issue type from the nodes text."""
        # Common issue types to look for
        issue_types = [
            'Expectation Mismatch',
            'Ordered by Mistake',
            'Wrong Item',
            'PDP Issues',
            'Compatibility Issues',
            'Part(s) Missing',
            'Empty Box received',
            'Different item received',
            'The item(s) are defective',
            'The item(s) are physically damaged',
            'The item(s) are not packed or sealed properly',
            'The item(s) are missing'
        ]
        
        for issue_type in issue_types:
            if issue_type.lower() in nodes_text.lower():
                return issue_type
        
        # If no specific issue type found, try to extract from the beginning
        lines = nodes_text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line and len(first_line) < 100:  # Reasonable length for issue type
                return first_line
        
        return None
    
    def _extract_voc_examples(self, voc_text: str) -> List[str]:
        """Extract VOC examples from the text."""
        if not voc_text or voc_text == 'nan':
            return []
        
        # Split by common VOC indicators
        voc_patterns = [
            r'VOC:\s*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'VOC:\s*(.*?)(?=\n\n|\n[A-Z]|$)',
        ]
        
        examples = []
        for pattern in voc_patterns:
            matches = re.findall(pattern, voc_text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Clean up the match
                cleaned = re.sub(r'\s+', ' ', match.strip())
                if cleaned and len(cleaned) > 10:  # Reasonable length
                    examples.append(cleaned)
        
        # If no patterns found, try to extract sentences
        if not examples:
            sentences = re.split(r'[.!?]\s*', voc_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:
                    examples.append(sentence)
        
        return examples[:5]  # Limit to 5 examples
    
    def _create_fallback_kb(self) -> None:
        """Create a fallback knowledge base if CSV parsing fails."""
        self.knowledge_base = {
            'Ordered by Mistake': {
                'voc_examples': [
                    'I accidentally ordered the wrong product',
                    'I ordered by mistake',
                    'I did not mean to order this'
                ],
                'resolutions': {
                    'gold': 'Service No',
                    'silver_bronze': 'Service No',
                    'new_iron': 'Service No'
                },
                'sop_details': 'Ordered by Mistake - Service No as per SOP'
            },
            'Expectation Mismatch': {
                'voc_examples': [
                    'The size is too small/big',
                    'I don\'t like the quality',
                    'I received different color'
                ],
                'resolutions': {
                    'gold': 'Replacement/RPU',
                    'silver_bronze': 'Service No',
                    'new_iron': 'Service No'
                },
                'sop_details': 'Expectation Mismatch - Check product details'
            }
        }
    
    def get_issue_types(self) -> List[str]:
        """Get list of all issue types."""
        return list(self.knowledge_base.keys())
    
    def get_voc_examples(self, issue_type: str) -> List[str]:
        """Get VOC examples for a specific issue type."""
        return self.knowledge_base.get(issue_type, {}).get('voc_examples', [])
    
    def get_resolution(self, issue_type: str, tier: str = 'gold') -> str:
        """Get resolution for a specific issue type and tier."""
        resolutions = self.knowledge_base.get(issue_type, {}).get('resolutions', {})
        return resolutions.get(tier, 'Service No')
    
    def get_sop_details(self, issue_type: str) -> str:
        """Get SOP details for a specific issue type."""
        return self.knowledge_base.get(issue_type, {}).get('sop_details', '')
    
    def find_best_match(self, user_input: str) -> Optional[str]:
        """Find the best matching issue type based on user input."""
        user_input_lower = user_input.lower()
        
        # Direct keyword matching
        keyword_mapping = {
            'mistake': 'Ordered by Mistake',
            'accidentally': 'Ordered by Mistake',
            'wrong product': 'Ordered by Mistake',
            'size': 'Expectation Mismatch',
            'color': 'Expectation Mismatch',
            'quality': 'Expectation Mismatch',
            'defective': 'The item(s) are defective',
            'damaged': 'The item(s) are physically damaged',
            'missing': 'The item(s) are missing',
            'empty box': 'Empty Box received',
            'wrong item': 'Wrong Item',
            'pdp': 'PDP Issues'
        }
        
        for keyword, issue_type in keyword_mapping.items():
            if keyword in user_input_lower:
                return issue_type
        
        # Fuzzy matching with VOC examples
        best_match = None
        best_score = 0
        
        for issue_type, data in self.knowledge_base.items():
            for voc_example in data.get('voc_examples', []):
                # Simple similarity check
                common_words = set(user_input_lower.split()) & set(voc_example.lower().split())
                if len(common_words) > best_score:
                    best_score = len(common_words)
                    best_match = issue_type
        
        return best_match if best_score > 0 else None
