// Wait for the DOM to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    const analyzeBtn = document.getElementById('analyze-btn');
    const urlInput = document.getElementById('urlInput');  
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');

    const form = document.getElementById('urlForm');
    const loadingStateDiv = document.createElement('div');
    loadingStateDiv.className = 'loading';
    loadingStateDiv.innerHTML = 'Analyzing comments...';

    analyzeBtn.addEventListener('click', async function() {
        const url = urlInput.value.trim();
        if (!url) {
            showError('Please enter a URL');
            return;
        }

        // Show loading state
        loadingDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';

        try {
            const response = await fetch('http://localhost:8000/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    url: url,
                    platform: 'youtube'
                })
            });

            const data = await response.json();
            console.log('Data:', data);

            // Hide loading
            loadingDiv.style.display = 'none';
            resultsDiv.style.display = 'block';

            if (!response.ok) {
                showError(data.detail || 'Failed to analyze comments');
                return;
            }

            if (data.error) {
                showError(data.error);
                return;
            }

            displayResults(data);

        } catch (error) {
            console.error('Error:', error);
            showError('Failed to connect to the server. Please try again.');
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Comments';
            loadingDiv.style.display = 'none';
        }
    });

    function showError(message) {
        const resultsDiv = document.getElementById('results');
        
        // Special handling for API key errors
        if (message.toLowerCase().includes('quota') || message.toLowerCase().includes('api key')) {
            resultsDiv.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ YouTube API Error</h3>
                    <p>${message}</p>
                    <div class="error-help">
                        <p>This error typically occurs when:</p>
                        <ul>
                            <li>The YouTube API key has expired</li>
                            <li>The daily quota has been exceeded</li>
                            <li>The API key is invalid</li>
                        </ul>
                        <p>Please try again later or contact support for assistance.</p>
                    </div>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    function displayResults(data) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '';

        // Display Think/Feel/Act insights
        const categories = ['think', 'feel', 'act'];
        categories.forEach(category => {
            const section = document.createElement('div');
            section.className = 'insight-section';
            section.innerHTML = `
                <h2>${category.toUpperCase()}</h2>
                ${(data[category] || []).map(insight => `
                    <div class="insight-card">
                        <p class="insight-text">${insight.text}</p>
                        <div class="engagement">
                            <span>👍 ${insight.likes || 0}</span>
                            <span>💬 ${insight.replies || 0}</span>
                        </div>
                    </div>
                `).join('')}
            `;
            resultsDiv.appendChild(section);
        });

        // Display Pain Points
        if (data.pain_points && data.pain_points.length > 0) {
            const painPointsSection = document.createElement('div');
            painPointsSection.className = 'insight-section';
            painPointsSection.innerHTML = `
                <h2>PAIN POINTS</h2>
                ${data.pain_points.map(point => `
                    <div class="insight-card">
                        <p class="insight-text">${point.text}</p>
                        <div class="engagement">
                            <span>💡 ${point.engagement || 0}</span>
                        </div>
                    </div>
                `).join('')}
            `;
            resultsDiv.appendChild(painPointsSection);
        }

        // Display Future Topics
        if (data.future_topics && data.future_topics.length > 0) {
            const topicsSection = document.createElement('div');
            topicsSection.className = 'insight-section';
            topicsSection.innerHTML = `
                <h2>POTENTIAL CONTENT TOPICS</h2>
                ${data.future_topics.map(topic => `
                    <div class="insight-card">
                        <p class="insight-text">${topic.topic || topic.text || ''}</p>
                    </div>
                `).join('')}
            `;
            resultsDiv.appendChild(topicsSection);
        }

        // Display Language Patterns
        if (data.language_patterns && data.language_patterns.length > 0) {
            const languageSection = document.createElement('div');
            languageSection.className = 'insight-section';
            languageSection.innerHTML = `
                <h2>LANGUAGE ALIGNMENT</h2>
                <div class="language-cloud">
                    ${data.language_patterns.map(pattern => `
                        <span class="language-term" style="font-size: ${Math.min((pattern.count || 1) * 0.5 + 1, 2)}em">
                            ${pattern.word}
                        </span>
                    `).join('')}
                </div>
            `;
            resultsDiv.appendChild(languageSection);
        }

        // Display Sentiment Analysis
        if (data.sentiment && (data.sentiment.positive || data.sentiment.negative)) {
            const sentimentSection = document.createElement('div');
            sentimentSection.className = 'insight-section';
            sentimentSection.innerHTML = `
                <h2>POSITIVE & NEGATIVE TAKES</h2>
                <div class="sentiment-container">
                    <div class="positive-sentiment">
                        <h3>Positive</h3>
                        ${(data.sentiment.positive || []).map(item => `
                            <div class="insight-card positive">
                                <p class="insight-text">${item.text}</p>
                                <div class="engagement">
                                    <span>💚 ${item.engagement || 0}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="negative-sentiment">
                        <h3>Negative</h3>
                        ${(data.sentiment.negative || []).map(item => `
                            <div class="insight-card negative">
                                <p class="insight-text">${item.text}</p>
                                <div class="engagement">
                                    <span>💔 ${item.engagement || 0}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            resultsDiv.appendChild(sentimentSection);
        }
    }

    function exportData(format) {
        const resultsDiv = document.getElementById('results');
        const data = resultsDiv.getAttribute('data-results');
        
        if (!data) {
            alert('No data to export');
            return;
        }

        const parsedData = JSON.parse(data);
        let content;
        let mimeType;
        let extension;

        if (format === 'json') {
            content = JSON.stringify(parsedData, null, 2);
            mimeType = 'application/json';
            extension = 'json';
        } else if (format === 'csv' || format === 'excel') {
            const comments = parsedData.data.comments;
            const headers = ['Text', 'Author', 'Likes', 'Platform', 'Timestamp'];
            const csvRows = [headers];

            comments.forEach(comment => {
                csvRows.push([
                    `"${comment.text.replace(/"/g, '""')}"`,
                    comment.author,
                    comment.likes,
                    'youtube',
                    comment.timestamp
                ]);
            });

            content = csvRows.map(row => row.join(',')).join('\\n');
            mimeType = format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel';
            extension = format === 'csv' ? 'csv' : 'xls';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `youtube_comments_analysis.${extension}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
});
