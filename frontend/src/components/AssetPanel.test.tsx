import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AssetPanel } from './AssetPanel';

// Mock the backend API
vi.mock('../api/backend', () => ({
  fetchAssets: vi.fn(),
}));

import { fetchAssets } from '../api/backend';
const mockFetchAssets = vi.mocked(fetchAssets);

describe('AssetPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no sessionId', () => {
    render(<AssetPanel sessionId={null} />);
    expect(screen.getByText('No session connected')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockFetchAssets.mockReturnValue(new Promise(() => {})); // never resolves
    render(<AssetPanel sessionId="s1" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders assets after loading', async () => {
    mockFetchAssets.mockResolvedValue({
      assets: [
        { id: 'a1', content_hash: 'h1', asset_type: 'image', metadata: { name: 'photo.jpg' } },
        { id: 'a2', content_hash: 'h2', asset_type: 'music', metadata: { name: 'bgm.mp3' } },
      ],
      total: 2,
    });

    render(<AssetPanel sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('photo.jpg')).toBeInTheDocument();
      expect(screen.getByText('bgm.mp3')).toBeInTheDocument();
    });
  });

  it('shows error message on failure', async () => {
    mockFetchAssets.mockRejectedValue(new Error('Network error'));
    render(<AssetPanel sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('shows empty message when no assets', async () => {
    mockFetchAssets.mockResolvedValue({ assets: [], total: 0 });
    render(<AssetPanel sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('No assets found')).toBeInTheDocument();
    });
  });

  it('renders filter buttons', async () => {
    mockFetchAssets.mockResolvedValue({ assets: [], total: 0 });
    render(<AssetPanel sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('all')).toBeInTheDocument();
      expect(screen.getByText('image')).toBeInTheDocument();
      expect(screen.getByText('video')).toBeInTheDocument();
      expect(screen.getByText('music')).toBeInTheDocument();
      expect(screen.getByText('sfx')).toBeInTheDocument();
    });
  });

  it('calls fetchAssets with filter when filter clicked', async () => {
    mockFetchAssets.mockResolvedValue({ assets: [], total: 0 });
    render(<AssetPanel sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('image')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('image'));
    await waitFor(() => {
      expect(mockFetchAssets).toHaveBeenCalledWith('s1', 'image');
    });
  });

  it('renders header with title', async () => {
    mockFetchAssets.mockResolvedValue({ assets: [], total: 0 });
    render(<AssetPanel sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('Assets')).toBeInTheDocument();
    });
  });
});
