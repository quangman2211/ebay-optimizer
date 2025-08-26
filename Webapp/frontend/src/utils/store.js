import { create } from 'zustand';
import { listingAPI, optimizationAPI } from '../services/api';

const useStore = create((set, get) => ({
  // State
  listings: [],
  selectedListing: null,
  loading: false,
  error: null,
  filters: {
    status: null,
    category: null,
  },
  optimizationResult: null,

  // Actions
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilters: (filters) => set({ filters }),
  
  // Listing actions
  fetchListings: async () => {
    set({ loading: true, error: null });
    try {
      console.log('📡 Fetching listings with filters:', get().filters);
      const response = await listingAPI.getAll(get().filters);
      console.log(`✅ Fetched ${response.data.length} listings`);
      set({ listings: response.data, loading: false });
    } catch (error) {
      console.error('❌ Fetch error:', error);
      set({ error: error.message, loading: false });
    }
  },

  selectListing: (listing) => set({ selectedListing: listing }),

  createListing: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await listingAPI.create(data);
      const listings = [...get().listings, response.data];
      set({ listings, loading: false });
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  updateListing: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const response = await listingAPI.update(id, data);
      const listings = get().listings.map(l => 
        l.id === id ? response.data : l
      );
      set({ listings, loading: false, selectedListing: response.data });
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  deleteListing: async (id) => {
    set({ loading: true, error: null });
    try {
      await listingAPI.delete(id);
      const listings = get().listings.filter(l => l.id !== id);
      set({ listings, loading: false, selectedListing: null });
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  syncWithSheets: async () => {
    set({ loading: true, error: null });
    try {
      console.log('🔄 Starting sync with Google Sheets...');
      const response = await listingAPI.sync();
      console.log('📊 Sync response:', response.data);
      
      // Use fresh data from sync response if available
      if (response.data.listings) {
        console.log(`✅ Updating state with ${response.data.listings.length} fresh listings`);
        set({ listings: response.data.listings, loading: false });
      } else {
        // Fallback to fetching fresh data
        console.log('⚠️ No listings in sync response, fetching fresh data...');
        await get().fetchListings();
      }
    } catch (error) {
      console.error('❌ Sync error:', error);
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  // Optimization actions
  optimizeListing: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await optimizationAPI.optimizeTitle(data);
      set({ optimizationResult: response.data, loading: false });
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  bulkOptimize: async (listingIds, options) => {
    set({ loading: true, error: null });
    try {
      const response = await optimizationAPI.bulkOptimize({
        listing_ids: listingIds,
        ...options
      });
      await get().fetchListings(); // Refresh listings
      set({ loading: false });
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  analyzeListing: async (id) => {
    set({ loading: true, error: null });
    try {
      const response = await optimizationAPI.analyzeListing(id);
      set({ loading: false });
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  clearOptimizationResult: () => set({ optimizationResult: null }),
}));

export default useStore;