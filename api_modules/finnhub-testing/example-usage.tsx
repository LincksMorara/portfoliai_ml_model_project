/**
 * Finnhub API Example Usage
 * 
 * This file demonstrates how to use the Finnhub API service and components
 * in your application.
 */

import React, { useState, useEffect } from 'react';
import { getCompanyNews } from './finnhubService';
import { FinnhubNewsCard, FinnhubNewsCardCompact, FinnhubNewsCardSkeleton } from './NewsCard';
import type { CompanyNewsResponse } from './finnhubService';

// ============================================================================
// Example 1: Basic API Usage (Standalone)
// ============================================================================

async function basicUsageExample() {
  try {
    // Fetch news for Apple in the last month
    const news: CompanyNewsResponse = await getCompanyNews('AAPL', '2024-01-01', '2024-01-31');
    
    console.log(`Found ${news.totalCount} articles for ${news.symbol}`);
    console.log(`Date range: ${news.fromDate} to ${news.toDate}`);
    
    // Display first 5 articles
    news.articles.slice(0, 5).forEach((article, index) => {
      console.log(`${index + 1}. ${article.headline}`);
      console.log(`   Source: ${article.source}`);
      console.log(`   URL: ${article.url}\n`);
    });
    
  } catch (error: any) {
    console.error('Error fetching news:', error.message);
  }
}

// ============================================================================
// Example 2: React Component with Loading States
// ============================================================================

interface NewsFeedProps {
  symbol: string;
  fromDate?: string;
  toDate?: string;
}

export function NewsFeedExample({ symbol, fromDate, toDate }: NewsFeedProps) {
  const [newsData, setNewsData] = useState<CompanyNewsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchNews() {
      setLoading(true);
      setError(null);
      
      try {
        const data = await getCompanyNews(symbol, fromDate, toDate);
        setNewsData(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchNews();
  }, [symbol, fromDate, toDate]);

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <FinnhubNewsCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-sm text-red-800">
          ⚠️ {error}
        </p>
      </div>
    );
  }

  if (!newsData || newsData.totalCount === 0) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
        <p className="text-sm text-gray-600">
          No news found for {symbol}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">
          Latest News: {newsData.symbol}
        </h2>
        <p className="text-sm text-gray-600">
          Showing {newsData.totalCount} articles from {newsData.fromDate} to {newsData.toDate}
        </p>
      </div>

      {newsData.articles.map((article, index) => (
        <FinnhubNewsCard key={index} article={article} />
      ))}
    </div>
  );
}

// ============================================================================
// Example 3: Compact News Grid
// ============================================================================

export function CompactNewsGridExample() {
  const [newsData, setNewsData] = useState<CompanyNewsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchNews() {
      try {
        const data = await getCompanyNews('TSLA'); // Tesla news
        setNewsData(data);
      } catch (error) {
        console.error('Failed to fetch news:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchNews();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <FinnhubNewsCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {newsData?.articles.slice(0, 9).map((article, index) => (
        <FinnhubNewsCardCompact key={index} article={article} />
      ))}
    </div>
  );
}

// ============================================================================
// Example 4: Single Article Display
// ============================================================================

interface SingleNewsProps {
  symbol: string;
}

export function SingleNewsExample({ symbol }: SingleNewsProps) {
  const [article, setArticle] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLatest() {
      try {
        const data = await getCompanyNews(symbol);
        // Get the most recent article
        if (data.articles.length > 0) {
          setArticle(data.articles[0]);
        }
      } catch (error) {
        console.error('Failed to fetch news:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchLatest();
  }, [symbol]);

  if (loading) {
    return <FinnhubNewsCardSkeleton />;
  }

  if (!article) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <p>No news available</p>
      </div>
    );
  }

  return <FinnhubNewsCard article={article} />;
}

// ============================================================================
// Example 5: Error Handling Best Practices
// ============================================================================

export async function robustErrorHandlingExample(symbol: string) {
  try {
    const news = await getCompanyNews(symbol);
    
    // Validate response
    if (!news || news.articles.length === 0) {
      return {
        success: false,
        message: 'No news available for this symbol',
        articles: []
      };
    }

    return {
      success: true,
      articles: news.articles,
      count: news.totalCount
    };

  } catch (error: any) {
    // Handle specific error types
    if (error.message.includes('API key')) {
      return {
        success: false,
        message: 'Configuration error: Please check your API key',
        articles: []
      };
    }

    if (error.message.includes('rate limit')) {
      return {
        success: false,
        message: 'Too many requests. Please try again later.',
        articles: []
      };
    }

    if (error.message.includes('timeout')) {
      return {
        success: false,
        message: 'Request timed out. Please try again.',
        articles: []
      };
    }

    return {
      success: false,
      message: `Failed to fetch news: ${error.message}`,
      articles: []
    };
  }
}

// ============================================================================
// Example 6: Date Range Selection
// ============================================================================

export function DateRangeExample() {
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-01-31');
  const [symbol, setSymbol] = useState('AAPL');
  const [newsData, setNewsData] = useState<CompanyNewsResponse | null>(null);

  const handleFetch = async () => {
    try {
      const data = await getCompanyNews(symbol, startDate, endDate);
      setNewsData(data);
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Custom Date Range</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Symbol
          </label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="AAPL"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={handleFetch}
            className="w-full bg-blue-600 text-white rounded-md px-4 py-2 hover:bg-blue-700"
          >
            Fetch News
          </button>
        </div>
      </div>

      {newsData && (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Found {newsData.totalCount} articles
          </p>
          {newsData.articles.map((article, index) => (
            <FinnhubNewsCard key={index} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Usage Instructions:
// ============================================================================
// 
// 1. Copy this entire file or parts of it to your project
// 2. Import the components you need:
//    import { NewsFeedExample } from './example-usage'
// 
// 3. Use in your pages:
//    export default function MyPage() {
//      return <NewsFeedExample symbol="AAPL" />
//    }
//
// 4. Or use the service directly:
//    import { getCompanyNews } from './finnhubService'
//    const news = await getCompanyNews('AAPL')
//
// ============================================================================

