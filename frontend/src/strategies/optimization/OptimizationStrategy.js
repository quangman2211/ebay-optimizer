/**
 * Optimization Strategy Pattern (Open/Closed Principle)
 * Open for extension: Can add new optimization algorithms
 * Closed for modification: Existing algorithms don't need changes
 */

/**
 * Base Optimization Strategy Interface
 * All optimization strategies must implement this interface
 */
class OptimizationStrategy {
  /**
   * Optimize a listing
   * @param {Object} listing - Listing to optimize
   * @returns {Promise<Object>} Optimized listing
   */
  async optimize(listing) {
    throw new Error('Must implement optimize method');
  }

  /**
   * Get strategy name
   * @returns {string} Strategy name
   */
  getName() {
    throw new Error('Must implement getName method');
  }

  /**
   * Get strategy description
   * @returns {string} Strategy description
   */
  getDescription() {
    throw new Error('Must implement getDescription method');
  }

  /**
   * Check if strategy can be applied to listing
   * @param {Object} listing - Listing to check
   * @returns {boolean} Whether strategy is applicable
   */
  canApply(listing) {
    return true; // Default: can apply to any listing
  }

  /**
   * Get estimated improvement score
   * @param {Object} listing - Listing to analyze
   * @returns {number} Estimated improvement (0-100)
   */
  getEstimatedImprovement(listing) {
    return 0; // Default: no improvement estimate
  }
}

/**
 * SEO Optimization Strategy
 * Focuses on search engine optimization for eBay listings
 */
class SEOOptimizationStrategy extends OptimizationStrategy {
  getName() {
    return 'seo_optimization';
  }

  getDescription() {
    return 'Tối ưu hóa SEO cho eBay - tối ưu tiêu đề, từ khóa và mô tả';
  }

  canApply(listing) {
    return listing && listing.title && listing.title.length > 0;
  }

  getEstimatedImprovement(listing) {
    let improvement = 0;
    
    // Check title optimization potential
    if (listing.title.length < 60) improvement += 20;
    if (!listing.title.includes('NEW') && listing.condition === 'new') improvement += 10;
    if (listing.keywords && listing.keywords.length < 5) improvement += 15;
    if (!listing.description || listing.description.length < 200) improvement += 25;
    
    return Math.min(improvement, 100);
  }

  async optimize(listing) {
    const optimized = { ...listing };

    // Optimize title
    optimized.title = this.optimizeTitle(listing.title, listing);
    
    // Optimize keywords
    optimized.keywords = this.extractKeywords(listing);
    
    // Optimize description
    optimized.description = this.enhanceDescription(listing.description, listing);
    
    // Calculate new SEO score
    optimized.seoScore = this.calculateSEOScore(optimized);
    
    return optimized;
  }

  optimizeTitle(title, listing) {
    let optimizedTitle = title;

    // Add NEW if condition is new and not already present
    if (listing.condition === 'new' && !title.toUpperCase().includes('NEW')) {
      optimizedTitle = `NEW ${optimizedTitle}`;
    }

    // Ensure title is within optimal length (60-80 characters)
    if (optimizedTitle.length > 80) {
      optimizedTitle = optimizedTitle.substring(0, 77) + '...';
    }

    // Front-load important keywords
    const category = listing.category || '';
    if (category && !optimizedTitle.toLowerCase().includes(category.toLowerCase())) {
      const words = optimizedTitle.split(' ');
      words.splice(1, 0, category);
      optimizedTitle = words.join(' ');
    }

    return optimizedTitle;
  }

  extractKeywords(listing) {
    const keywords = new Set();
    
    // Extract from title
    const titleWords = (listing.title || '').toLowerCase().split(/\s+/);
    titleWords.forEach(word => {
      if (word.length > 3 && !this.isStopWord(word)) {
        keywords.add(word);
      }
    });

    // Extract from category
    if (listing.category) {
      keywords.add(listing.category.toLowerCase());
    }

    // Add condition
    if (listing.condition) {
      keywords.add(listing.condition.toLowerCase());
    }

    return Array.from(keywords).slice(0, 10); // Limit to 10 keywords
  }

  enhanceDescription(description, listing) {
    let enhanced = description || '';

    // Add structured format if not present
    if (!enhanced.includes('FEATURES:') && !enhanced.includes('KEY FEATURES')) {
      enhanced = this.addStructuredFormat(enhanced, listing);
    }

    // Add emoji if not present
    if (!enhanced.includes('✓') && !enhanced.includes('🔥')) {
      enhanced = this.addEmojis(enhanced);
    }

    return enhanced;
  }

  addStructuredFormat(description, listing) {
    const features = [
      `✓ Brand new ${listing.condition || 'condition'}`,
      '✓ Fast and secure shipping',
      '✓ 100% authentic guaranteed',
      '✓ Professional packaging'
    ];

    return `🔥 KEY FEATURES:
${features.join('\n')}

📦 DESCRIPTION:
${description}

💰 BEST PRICE GUARANTEED!`;
  }

  addEmojis(description) {
    return description
      .replace(/fast shipping/gi, '⚡ Fast shipping')
      .replace(/new/gi, '🆕 New')
      .replace(/guarantee/gi, '✅ Guarantee');
  }

  calculateSEOScore(listing) {
    let score = 0;

    // Title optimization (40 points)
    if (listing.title) {
      if (listing.title.length >= 60 && listing.title.length <= 80) score += 20;
      if (listing.title.includes('NEW') || listing.title.includes('Brand')) score += 10;
      if (listing.title.match(/\d+/)) score += 10; // Contains numbers
    }

    // Keywords (25 points)
    if (listing.keywords && listing.keywords.length >= 5) score += 25;

    // Description (25 points)
    if (listing.description) {
      if (listing.description.length >= 200) score += 15;
      if (listing.description.includes('✓') || listing.description.includes('🔥')) score += 10;
    }

    // Category (10 points)
    if (listing.category) score += 10;

    return Math.min(score, 100);
  }

  isStopWord(word) {
    const stopWords = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'];
    return stopWords.includes(word.toLowerCase());
  }
}

/**
 * AI Optimization Strategy
 * Uses AI/ML algorithms for optimization
 */
class AIOptimizationStrategy extends OptimizationStrategy {
  getName() {
    return 'ai_optimization';
  }

  getDescription() {
    return 'Tối ưu hóa sử dụng AI - phân tích thị trường và đề xuất thông minh';
  }

  canApply(listing) {
    return listing && listing.category; // Needs category for AI analysis
  }

  getEstimatedImprovement(listing) {
    // AI can potentially provide higher improvements
    let improvement = 30; // Base AI improvement
    
    if (listing.performanceScore < 50) improvement += 40;
    if (!listing.keywords || listing.keywords.length === 0) improvement += 20;
    
    return Math.min(improvement, 100);
  }

  async optimize(listing) {
    const optimized = { ...listing };

    // Simulate AI optimization (in real implementation, this would call AI service)
    optimized.title = await this.aiOptimizeTitle(listing);
    optimized.description = await this.aiGenerateDescription(listing);
    optimized.keywords = await this.aiExtractKeywords(listing);
    optimized.category = await this.aiSuggestCategory(listing);
    
    // Calculate AI-based performance score
    optimized.performanceScore = this.calculateAIScore(optimized);
    
    return optimized;
  }

  async aiOptimizeTitle(listing) {
    // Simulate AI title optimization
    const category = listing.category || 'Product';
    const condition = listing.condition || 'new';
    const brand = this.extractBrand(listing.title) || 'Premium';
    
    return `${brand} ${category} - ${condition.toUpperCase()} - Fast Shipping - Best Price`;
  }

  async aiGenerateDescription(listing) {
    // Simulate AI description generation
    return `🤖 AI-OPTIMIZED LISTING

🔥 PREMIUM ${(listing.category || 'PRODUCT').toUpperCase()}:
• High-quality ${listing.condition || 'new'} condition
• Professionally inspected and tested
• Market-leading specifications
• Competitive pricing

📊 MARKET ANALYSIS:
✓ Top 5% seller rating required
✓ Optimized for maximum visibility
✓ Keyword-rich content for search ranking

💡 WHY CHOOSE THIS ITEM:
• AI-verified authenticity
• Performance-optimized listing
• Data-driven pricing strategy
• Enhanced buyer experience

⚡ FAST SHIPPING & EXCELLENT SERVICE!`;
  }

  async aiExtractKeywords(listing) {
    // Simulate AI keyword extraction
    const baseKeywords = [
      listing.category?.toLowerCase(),
      listing.condition,
      'premium',
      'fast shipping',
      'best price',
      'authentic',
      'guaranteed'
    ].filter(Boolean);

    return baseKeywords.slice(0, 8);
  }

  async aiSuggestCategory(listing) {
    // Simulate AI category suggestion
    return listing.category || 'Electronics'; // Would use ML model in real implementation
  }

  extractBrand(title) {
    // Simple brand extraction logic
    const brands = ['Apple', 'Samsung', 'Sony', 'Nintendo', 'Microsoft', 'Canon', 'Nikon'];
    return brands.find(brand => title.includes(brand)) || null;
  }

  calculateAIScore(listing) {
    // AI-based scoring algorithm
    let score = 50; // Base score

    if (listing.title && listing.title.includes('AI-OPTIMIZED')) score += 20;
    if (listing.keywords && listing.keywords.length >= 6) score += 20;
    if (listing.description && listing.description.includes('🤖')) score += 10;

    return Math.min(score, 100);
  }
}

/**
 * Market-Based Optimization Strategy
 * Optimizes based on market trends and competitor analysis
 */
class MarketOptimizationStrategy extends OptimizationStrategy {
  getName() {
    return 'market_optimization';
  }

  getDescription() {
    return 'Tối ưu hóa theo thị trường - phân tích đối thủ và xu hướng giá';
  }

  canApply(listing) {
    return listing && listing.currentPrice > 0;
  }

  getEstimatedImprovement(listing) {
    let improvement = 15; // Base market improvement
    
    // Check if price seems off-market
    if (listing.currentPrice > listing.originalPrice * 1.5) improvement += 25;
    if (!listing.category || listing.category === 'Uncategorized') improvement += 20;
    
    return Math.min(improvement, 100);
  }

  async optimize(listing) {
    const optimized = { ...listing };

    // Optimize pricing based on market analysis
    optimized.currentPrice = await this.optimizePrice(listing);
    
    // Suggest better category based on market data
    optimized.category = await this.suggestBestCategory(listing);
    
    // Add market-based keywords
    optimized.keywords = await this.addMarketKeywords(listing);
    
    // Calculate market score
    optimized.marketScore = this.calculateMarketScore(optimized);
    
    return optimized;
  }

  async optimizePrice(listing) {
    // Simulate market price optimization
    const currentPrice = listing.currentPrice;
    const originalPrice = listing.originalPrice || currentPrice;
    
    // Simple market-based pricing (would use real market data)
    const marketMultiplier = this.getMarketMultiplier(listing.category);
    const optimizedPrice = originalPrice * marketMultiplier;
    
    return Math.round(optimizedPrice * 100) / 100;
  }

  async suggestBestCategory(listing) {
    // Simulate category optimization based on market performance
    const categoryMap = {
      'Electronics': 'Consumer Electronics',
      'Fashion': 'Clothing, Shoes & Accessories',
      'Home': 'Home & Garden',
      'Sports': 'Sporting Goods'
    };
    
    return categoryMap[listing.category] || listing.category;
  }

  async addMarketKeywords(listing) {
    const existingKeywords = listing.keywords || [];
    const marketKeywords = [
      'trending',
      'popular',
      'bestseller',
      'market leader',
      'competitive price'
    ];
    
    return [...existingKeywords, ...marketKeywords].slice(0, 10);
  }

  getMarketMultiplier(category) {
    // Market multipliers based on category performance
    const multipliers = {
      'Electronics': 1.15,
      'Fashion': 1.25,
      'Home & Garden': 1.10,
      'Sports': 1.20,
      'default': 1.12
    };
    
    return multipliers[category] || multipliers.default;
  }

  calculateMarketScore(listing) {
    let score = 60; // Base market score

    // Price competitiveness
    if (listing.currentPrice <= listing.originalPrice * 1.2) score += 20;
    
    // Category optimization
    if (listing.category && !listing.category.includes('Uncategorized')) score += 15;
    
    // Keyword market relevance
    if (listing.keywords && listing.keywords.some(k => k.includes('trending'))) score += 5;
    
    return Math.min(score, 100);
  }
}

/**
 * Optimization Strategy Factory
 * Manages strategy creation and selection (Factory Pattern + OCP)
 */
class OptimizationStrategyFactory {
  constructor() {
    this.strategies = new Map();
    
    // Register default strategies
    this.register(new SEOOptimizationStrategy());
    this.register(new AIOptimizationStrategy());
    this.register(new MarketOptimizationStrategy());
  }

  /**
   * Register new optimization strategy
   * Open for extension: Can add new strategies without modifying existing code
   * @param {OptimizationStrategy} strategy - Strategy instance
   */
  register(strategy) {
    if (!(strategy instanceof OptimizationStrategy)) {
      throw new Error('Strategy must extend OptimizationStrategy');
    }
    
    this.strategies.set(strategy.getName(), strategy);
  }

  /**
   * Get strategy by name
   * @param {string} name - Strategy name
   * @returns {OptimizationStrategy|null}
   */
  getStrategy(name) {
    return this.strategies.get(name) || null;
  }

  /**
   * Get all available strategies
   * @returns {Array<OptimizationStrategy>}
   */
  getAllStrategies() {
    return Array.from(this.strategies.values());
  }

  /**
   * Get applicable strategies for a listing
   * @param {Object} listing - Listing to check
   * @returns {Array<OptimizationStrategy>}
   */
  getApplicableStrategies(listing) {
    return this.getAllStrategies().filter(strategy => strategy.canApply(listing));
  }

  /**
   * Get best strategy for a listing
   * @param {Object} listing - Listing to optimize
   * @returns {OptimizationStrategy|null}
   */
  getBestStrategy(listing) {
    const applicable = this.getApplicableStrategies(listing);
    
    if (applicable.length === 0) return null;
    
    // Return strategy with highest estimated improvement
    return applicable.reduce((best, current) => 
      current.getEstimatedImprovement(listing) > best.getEstimatedImprovement(listing) 
        ? current 
        : best
    );
  }

  /**
   * Create optimization context
   * @param {string} strategyName - Strategy name
   * @returns {OptimizationContext}
   */
  createContext(strategyName) {
    const strategy = this.getStrategy(strategyName);
    return new OptimizationContext(strategy);
  }
}

/**
 * Optimization Context (Strategy Pattern Implementation)
 */
class OptimizationContext {
  constructor(strategy) {
    this.strategy = strategy;
  }

  /**
   * Set optimization strategy
   * @param {OptimizationStrategy} strategy - Strategy instance
   */
  setStrategy(strategy) {
    this.strategy = strategy;
  }

  /**
   * Execute optimization
   * @param {Object} listing - Listing to optimize
   * @returns {Promise<Object>}
   */
  async optimize(listing) {
    if (!this.strategy) {
      throw new Error('No optimization strategy set');
    }
    
    return this.strategy.optimize(listing);
  }

  /**
   * Get strategy info
   * @returns {Object}
   */
  getStrategyInfo() {
    if (!this.strategy) return null;
    
    return {
      name: this.strategy.getName(),
      description: this.strategy.getDescription()
    };
  }
}

// Export factory instance and classes
export { 
  OptimizationStrategy,
  SEOOptimizationStrategy,
  AIOptimizationStrategy,
  MarketOptimizationStrategy,
  OptimizationStrategyFactory,
  OptimizationContext
};

// Export default factory instance
export default new OptimizationStrategyFactory();