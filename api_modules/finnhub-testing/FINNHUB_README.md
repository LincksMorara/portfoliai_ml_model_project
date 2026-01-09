# Finnhub API Testing Module

A standalone module for testing and integrating Finnhub Company News API into your project.

## 📋 Overview

This module provides a complete implementation for fetching and displaying company news from the Finnhub API. It includes:
- Clean API service with error handling
- Reusable React components
- Type-safe TypeScript interfaces
- Loading states and skeletons
- Utility functions for formatting

## 🚀 Quick Start

### 1. Copy Files

Copy the entire `finnhub-testing` folder to your project.

### 2. Install Dependencies

```bash
npm install axios
# or
yarn add axios
```

### 3. Set Environment Variable

Create or update your `.env.local` file:

```env
NEXT_PUBLIC_FINNHUB_API_KEY=your_finnhub_api_key_here
```

**Get your free API key:** https://finnhub.io/register

### 4. Use in Your Project

```typescript
import { getCompanyNews } from './finnhub-testing/finnhubService'

// Fetch news
const news = await getCompanyNews('AAPL', '2024-01-01', '2024-01-31')
console.log(news.articles)
```

## 📁 File Structure

```
finnhub-testing/
├── FINNHUB_README.md          # This file
├── finnhubService.ts          # API service and utilities
├── NewsCard.tsx               # News card components
└── example-usage.tsx          # Example implementation
```

## 🔑 API Key Setup

1. **Sign up:** Go to https://finnhub.io/register
2. **Get key:** Copy your free API key from dashboard
3. **Add to `.env.local`:** `NEXT_PUBLIC_FINNHUB_API_KEY=paste_key_here`
4. **Rate limits:** Free tier = 60 calls/minute

## 📊 API Documentation

### `getCompanyNews(symbol, fromDate?, toDate?)`

Fetches company news articles for a given stock symbol.

**Parameters:**
- `symbol` (string, required): Stock ticker symbol (e.g., 'AAPL')
- `fromDate` (string, optional): Start date in 'YYYY-MM-DD' format (defaults to 7 days ago)
- `toDate` (string, optional): End date in 'YYYY-MM-DD' format (defaults to today)

**Returns:**
```typescript
{
  articles: CompanyNewsArticle[],
  totalCount: number,
  symbol: string,
  fromDate: string,
  toDate: string
}
```

**Example:**
```typescript
const news = await getCompanyNews('TSLA', '2024-01-01', '2024-01-31')
console.log(`Found ${news.totalCount} articles`)
news.articles.forEach(article => {
  console.log(article.headline)
})
```

### Article Structure

```typescript
interface CompanyNewsArticle {
  headline: string      // News headline
  source: string        // News source name
  datetime: number      // Unix timestamp
  summary: string       // Article summary
  related: string       // Related ticker symbols
  url: string          // Full article URL
}
```

## 🎨 Components

### `FinnhubNewsCard`

Full-featured news card component.

```tsx
import { FinnhubNewsCard } from './NewsCard'

<FinnhubNewsCard 
  article={article} 
  className="mb-4" 
/>
```

### `FinnhubNewsCardCompact`

Compact news card for smaller spaces.

```tsx
import { FinnhubNewsCardCompact } from './NewsCard'

<FinnhubNewsCardCompact 
  article={article} 
  className="h-full" 
/>
```

### `FinnhubNewsCardSkeleton`

Loading skeleton for better UX.

```tsx
import { FinnhubNewsCardSkeleton } from './NewsCard'

{isLoading && <FinnhubNewsCardSkeleton />}
```

## 🛠️ Utility Functions

### `formatNewsDate(datetime)`

Formats Unix timestamp to readable date.

```typescript
import { formatNewsDate } from './finnhubService'

const date = formatNewsDate(1704067200) // "Dec 1, 2023"
```

### `truncateText(text, maxLength)`

Truncates text to specified length with ellipsis.

```typescript
import { truncateText } from './finnhubService'

const short = truncateText(longText, 100) // "..."
```

### `parseRelatedTickers(related)`

Parses comma-separated ticker symbols.

```typescript
import { parseRelatedTickers } from './finnhubService'

const tickers = parseRelatedTickers("AAPL,MSFT,GOOGL")
// ["AAPL", "MSFT", "GOOGL"]
```

## ⚠️ Error Handling

The service handles common errors:

- **401 Unauthorized:** Invalid API key
- **429 Too Many Requests:** Rate limit exceeded
- **404 Not Found:** No news available
- **Timeout:** Request timeout (10 seconds)
- **Network:** Connection issues

**Example:**
```typescript
try {
  const news = await getCompanyNews('AAPL')
} catch (error) {
  console.error('Failed to fetch news:', error.message)
  // Handle error appropriately
}
```

## 📝 Example Usage

See `example-usage.tsx` for complete working examples including:
- Basic news fetching
- Using components in React
- Error handling
- Loading states
- Custom styling

## 🔄 Migration Guide

### From This Project

If you're copying from the PortfoliAI project:

1. **Copy files:** All files from `api_modules/finnhub-testing/`
2. **Update imports:** Change any `@/lib/services` imports to relative paths
3. **Check dependencies:** Ensure `axios` is installed
4. **Environment:** Add FINNHUB_API_KEY to your `.env.local`
5. **Test:** Run the example usage file

### Adapting to Your Framework

**For Next.js:**
- Works as-is
- Use `NEXT_PUBLIC_` prefix for environment variables

**For React/Vite:**
- Change `NEXT_PUBLIC_` to `VITE_`
- Update environment variable references

**For Node.js Backend:**
- Can use `finnhubService.ts` as-is
- Remove React components
- Import service directly

## 🧪 Testing

Test the API integration:

```bash
# Using curl
curl "https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2024-01-01&to=2024-01-31&token=YOUR_API_KEY"

# Using the service
import { getCompanyNews } from './finnhubService'
const result = await getCompanyNews('AAPL')
console.log(result)
```

## 📚 Additional Resources

- **Finnhub Docs:** https://finnhub.io/docs/api/company-news
- **API Playground:** https://finnhub.io/docs/api
- **Support:** https://finnhub.io/support

## ⚡ Performance Tips

1. **Cache results:** Store news data for 5-10 minutes
2. **Lazy load:** Only fetch when user requests news
3. **Pagination:** Implement pagination for large result sets
4. **Debounce:** Debounce search inputs
5. **Skeletons:** Show loading states for better UX

## 🐛 Troubleshooting

### "API key is not configured"
- Check `.env.local` file exists
- Verify `NEXT_PUBLIC_FINNHUB_API_KEY` is set
- Restart dev server after adding env variables

### "Rate limit exceeded"
- Free tier = 60 calls/minute
- Implement caching
- Consider upgrading plan

### "No news found"
- Symbol might not have news in date range
- Expand date range
- Some symbols have limited news coverage

### CORS errors
- Run server-side or use Next.js API routes
- Don't call API directly from browser (public keys)

## 📄 License

This module is part of the PortfoliAI project and can be used freely for integration purposes.

## 🤝 Support

For issues with this module:
1. Check the example-usage.tsx file
2. Review Finnhub API documentation
3. Check browser console for error messages

