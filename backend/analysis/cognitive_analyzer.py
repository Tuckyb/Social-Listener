import re
from typing import List, Dict, Any
from collections import Counter
import logging
from textblob import TextBlob

logger = logging.getLogger(__name__)

class MarketingInsightAnalyzer:
    def __init__(self):
        # Marketing-focused patterns
        self.patterns = {
            'think': [
                r'(?i)\bthink\b|\bbelieve\b|\btheory\b|\bwonder\b|\bmaybe\b|\bperhaps\b|\bpossibly\b|\bspeculate\b',
                r'(?i)could be|might be|seems like|appears to|probably|likely|assuming|guess',
                r'(?i)what if|imagine if|consider|predict|expect|anticipate|forecast|theorize',
            ],
            'feel': [
                r'(?i)love|hate|amazing|terrible|awesome|awful|great|bad|disappointed|impressed',
                r'(?i)excited|worried|concerned|happy|sad|angry|frustrated|pleased|enjoy|annoyed',
                r'(?i)cant wait|looking forward|hope|wish|miss|glad|favorite|best|worst',
            ],
            'act': [
                r'(?i)\buse\b|\bbuy\b|\bplay\b|\btry\b|\bstart\b|\bstop\b|\bchange\b|\bswitch\b',
                r'(?i)going to|will|planning to|intend to|about to|decided to|committed to',
                r'(?i)bought|purchased|ordered|downloaded|installed|uninstalled|removed|added',
            ]
        }
        
        # Pain points patterns
        self.pain_patterns = [
            r'(?i)problem|issue|difficult|hard|confusing|unclear|missing|need|lack|wish|should have',
            r'(?i)cant|cannot|unable|impossible|frustrated|annoying|disappointing|limited|broken',
            r'(?i)expensive|costly|overpriced|waste|not worth|better if|improve|fix|bug|error'
        ]
        
        # Positive/negative sentiment indicators
        self.positive_patterns = [
            r'(?i)love|great|amazing|awesome|excellent|perfect|best|fantastic|wonderful|brilliant',
            r'(?i)helpful|useful|worth|valuable|impressive|good|nice|enjoy|pleased|happy'
        ]
        self.negative_patterns = [
            r'(?i)hate|terrible|awful|worst|bad|poor|horrible|useless|waste|disappointed',
            r'(?i)annoying|frustrating|confusing|difficult|expensive|costly|broken|buggy|error'
        ]

    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"Starting analysis of {len(comments)} comments")
        
        results = {
            'think': [],
            'feel': [],
            'act': [],
            'trending_topics': [],
            'high_engagement_comments': [],
            'pain_points': [],
            'future_topics': [],
            'language_patterns': [],
            'sentiment': {
                'positive': [],
                'negative': []
            }
        }

        try:
            # Sort comments by engagement
            sorted_comments = sorted(
                comments, 
                key=lambda x: (x.get('likes', 0) + len(x.get('replies', [])), x.get('likes', 0)), 
                reverse=True
            )

            # Collect common phrases for language analysis
            all_text = ' '.join(comment['text'].lower() for comment in comments)
            words = re.findall(r'\b\w+\b', all_text)
            word_freq = Counter(words)
            results['language_patterns'] = [
                {'word': word, 'count': count}
                for word, count in word_freq.most_common(10)
                if len(word) > 3  # Filter out short words
            ]

            # Analyze each comment
            for comment in comments:
                text = comment['text'].lower()
                engagement = comment.get('likes', 0) + len(comment.get('replies', []))
                
                # Only process comments with some engagement or substance
                if len(text) > 30:
                    # Think/Feel/Act categorization
                    categorized = False
                    for category, patterns in self.patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, text):
                                if engagement > 2:  # Minimum engagement threshold
                                    results[category].append({
                                        'text': comment['text'],
                                        'likes': comment.get('likes', 0),
                                        'replies': len(comment.get('replies', [])),
                                        'author': comment.get('author', 'Anonymous')
                                    })
                                categorized = True
                                break
                        if categorized:
                            break

                    # Pain points analysis
                    for pattern in self.pain_patterns:
                        if re.search(pattern, text):
                            results['pain_points'].append({
                                'text': comment['text'],
                                'engagement': engagement
                            })
                            break

                    # Sentiment analysis
                    blob = TextBlob(text)
                    if blob.sentiment.polarity > 0.3:
                        results['sentiment']['positive'].append({
                            'text': comment['text'],
                            'engagement': engagement
                        })
                    elif blob.sentiment.polarity < -0.3:
                        results['sentiment']['negative'].append({
                            'text': comment['text'],
                            'engagement': engagement
                        })

            # Extract potential future topics
            topic_phrases = []
            for comment in comments:
                sentences = comment['text'].split('.')
                for sentence in sentences:
                    if re.search(r'(?i)should|could|would|wish|hope|want|need|expect|future|next|upcoming', sentence):
                        topic_phrases.append(sentence.strip())

            results['future_topics'] = [
                {'topic': phrase, 'engagement': 1}
                for phrase in topic_phrases[:5]
            ]

            # Keep only top 4 most engaging items for think/feel/act
            for category in ['think', 'feel', 'act']:
                results[category] = sorted(
                    results[category],
                    key=lambda x: (x['likes'] + x['replies']),
                    reverse=True
                )[:4]

            # Keep top items for other categories
            results['pain_points'] = sorted(
                results['pain_points'],
                key=lambda x: x['engagement'],
                reverse=True
            )[:5]

            results['sentiment']['positive'] = sorted(
                results['sentiment']['positive'],
                key=lambda x: x['engagement'],
                reverse=True
            )[:3]

            results['sentiment']['negative'] = sorted(
                results['sentiment']['negative'],
                key=lambda x: x['engagement'],
                reverse=True
            )[:3]

            logger.info(f"Analysis complete. Found {len(results['think'])} think, {len(results['feel'])} feel, {len(results['act'])} act insights")
            return results

        except Exception as e:
            logger.error(f"Error during comment analysis: {str(e)}")
            return {
                'think': [],
                'feel': [],
                'act': [],
                'trending_topics': [],
                'high_engagement_comments': [],
                'pain_points': [],
                'future_topics': [],
                'language_patterns': [],
                'sentiment': {'positive': [], 'negative': []}
            }
