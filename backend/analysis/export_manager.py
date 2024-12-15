import pandas as pd
from typing import List, Dict, Any
import json
from datetime import datetime
import os

class ExportManager:
    def __init__(self):
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)

    def _prepare_data(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare data for export by flattening the structure"""
        export_data = []
        
        # Basic post information
        post_info = {
            'post_title': data.get('title', ''),
            'post_author': data.get('author', ''),
            'post_date': data.get('publish_date', ''),
            'post_likes': data.get('likes', 0),
            'platform': data.get('platform', ''),
            'url': data.get('url', ''),
            'total_comments': data.get('comment_count', 0)
        }
        
        # Analysis summary
        analysis_summary = {
            'overall_think_count': analysis['think']['total'],
            'overall_feel_count': analysis['feel']['total'],
            'overall_act_count': analysis['act']['total'],
            'average_sentiment_polarity': analysis['sentiment']['average_polarity'],
            'average_sentiment_subjectivity': analysis['sentiment']['average_subjectivity'],
            'dominant_category': max(analysis['category_distribution'].items(), key=lambda x: x[1])[0],
            'top_phrases': ', '.join([f"{phrase}({count})" for phrase, count in analysis['common_phrases'][:5]])
        }
        
        # Process each comment
        comments = data.get('comments', [])
        for comment in comments:
            comment_data = {
                **post_info,  # Include post information
                **analysis_summary,  # Include analysis summary
                'comment_id': comment.get('id', ''),
                'comment_author': comment.get('author', ''),
                'comment_text': comment.get('text', ''),
                'comment_timestamp': comment.get('timestamp', ''),
                'comment_likes': comment.get('likes', 0),
                'cognitive_category': comment.get('analysis', {}).get('overall_category', ''),
                'think_indicators': comment.get('analysis', {}).get('think', {}).get('count', 0),
                'feel_indicators': comment.get('analysis', {}).get('feel', {}).get('count', 0),
                'act_indicators': comment.get('analysis', {}).get('act', {}).get('count', 0),
                'sentiment_polarity': comment.get('analysis', {}).get('sentiment', {}).get('polarity', 0),
                'sentiment_subjectivity': comment.get('analysis', {}).get('sentiment', {}).get('subjectivity', 0)
            }
            export_data.append(comment_data)
        
        return export_data

    def export_to_excel(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Export data to Excel with multiple sheets"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/social_analysis_{data['platform']}_{timestamp}.xlsx"
        
        # Prepare the data
        export_data = self._prepare_data(data, analysis)
        
        # Create Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Comments sheet
            df_comments = pd.DataFrame(export_data)
            df_comments.to_excel(writer, sheet_name='Comments Analysis', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Platform',
                    'Total Comments',
                    'Think Indicators',
                    'Feel Indicators',
                    'Act Indicators',
                    'Average Sentiment',
                    'Dominant Category',
                    'Top Phrases'
                ],
                'Value': [
                    data.get('platform', ''),
                    data.get('comment_count', 0),
                    analysis['think']['total'],
                    analysis['feel']['total'],
                    analysis['act']['total'],
                    f"{analysis['sentiment']['average_polarity']:.2f}",
                    max(analysis['category_distribution'].items(), key=lambda x: x[1])[0],
                    '\n'.join([f"{phrase}({count})" for phrase, count in analysis['common_phrases'][:5]])
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Examples sheet
            examples_data = []
            for category in ['think', 'feel', 'act']:
                for example in analysis[category]['examples']:
                    examples_data.append({
                        'Category': category.capitalize(),
                        'Example': example
                    })
            df_examples = pd.DataFrame(examples_data)
            df_examples.to_excel(writer, sheet_name='Examples', index=False)
        
        return filename

    def export_to_json(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Export data to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/social_analysis_{data['platform']}_{timestamp}.json"
        
        export_data = {
            'post_info': {
                'title': data.get('title', ''),
                'author': data.get('author', ''),
                'publish_date': data.get('publish_date', ''),
                'likes': data.get('likes', 0),
                'platform': data.get('platform', ''),
                'url': data.get('url', ''),
                'comment_count': data.get('comment_count', 0)
            },
            'analysis_summary': {
                'cognitive_analysis': {
                    'think': analysis['think'],
                    'feel': analysis['feel'],
                    'act': analysis['act'],
                    'category_distribution': analysis['category_distribution']
                },
                'sentiment_analysis': analysis['sentiment'],
                'common_phrases': analysis['common_phrases']
            },
            'comments': data.get('comments', [])
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename

    def export_to_csv(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Export data to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/social_analysis_{data['platform']}_{timestamp}.csv"
        
        # Prepare the data
        export_data = self._prepare_data(data, analysis)
        
        # Create DataFrame and export to CSV
        df = pd.DataFrame(export_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        return filename
