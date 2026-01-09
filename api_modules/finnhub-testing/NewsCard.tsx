import React from 'react';
import { formatNewsDate, truncateText, parseRelatedTickers } from './finnhubService';
import type { CompanyNewsArticle } from './finnhubService';

interface NewsCardProps {
  article: CompanyNewsArticle;
  className?: string;
  style?: React.CSSProperties;
}

export function FinnhubNewsCard({ article, className = '', style }: NewsCardProps) {
  const formattedDate = formatNewsDate(article.datetime);
  const truncatedSummary = truncateText(article.summary, 250);
  const relatedTickers = parseRelatedTickers(article.related);

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200 ${className}`} style={style}>
      {/* Header */}
      <div className="p-4 pb-3">
        <h3 className="text-lg font-bold text-gray-900 leading-tight mb-2">
          {article.headline}
        </h3>
        
        {/* Metadata Row */}
        <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
          <span className="font-medium">{article.source}</span>
          <span>{formattedDate}</span>
        </div>
      </div>

      {/* Summary */}
      <div className="px-4 pb-3">
        <p className="text-sm text-gray-700 leading-relaxed">
          {truncatedSummary}
        </p>
      </div>

      {/* Related Tickers */}
      {relatedTickers.length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex flex-wrap gap-1">
            <span className="text-xs text-gray-500">Related:</span>
            {relatedTickers.map((ticker, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {ticker}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="px-4 pb-4 pt-2 border-t border-gray-100">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors duration-200"
        >
          Read Full Article
          <svg
            className="ml-1 w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>
      </div>
    </div>
  );
}

// Compact variant for smaller spaces
export function FinnhubNewsCardCompact({ article, className = '', style }: NewsCardProps) {
  const formattedDate = formatNewsDate(article.datetime);
  const truncatedSummary = truncateText(article.summary, 150);
  const relatedTickers = parseRelatedTickers(article.related);

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200 ${className}`} style={style}>
      <div className="p-3">
        <h3 className="text-base font-bold text-gray-900 leading-tight mb-2 line-clamp-2">
          {article.headline}
        </h3>
        
        <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
          <span className="font-medium">{article.source}</span>
          <span>{formattedDate}</span>
        </div>

        <p className="text-sm text-gray-700 leading-relaxed mb-2 line-clamp-3">
          {truncatedSummary}
        </p>

        {relatedTickers.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {relatedTickers.slice(0, 3).map((ticker, index) => (
              <span
                key={index}
                className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
              >
                {ticker}
              </span>
            ))}
            {relatedTickers.length > 3 && (
              <span className="text-xs text-gray-500">+{relatedTickers.length - 3} more</span>
            )}
          </div>
        )}

        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors duration-200"
        >
          Read More →
        </a>
      </div>
    </div>
  );
}

// Loading skeleton for NewsCard
export function FinnhubNewsCardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      <div className="p-4 pb-3">
        <div className="h-6 bg-gray-200 rounded mb-2 animate-pulse"></div>
        <div className="flex items-center justify-between mb-3">
          <div className="h-4 w-20 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </div>
      
      <div className="px-4 pb-3">
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </div>
      
      <div className="px-4 pb-4 pt-2 border-t border-gray-100">
        <div className="h-4 w-32 bg-gray-200 rounded animate-pulse"></div>
      </div>
    </div>
  );
}

