// =============================================================================
// Tests: use-auth.ts — Authentication state management
// =============================================================================

import { renderHook, act, waitFor } from "@testing-library/react";

// Must mock before importing
const mockGetUser = jest.fn();
const mockSignOut = jest.fn();
const mockOnAuthStateChange = jest.fn();

jest.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getUser: mockGetUser,
      signOut: mockSignOut,
      onAuthStateChange: mockOnAuthStateChange,
    },
  }),
}));

import { useAuth } from "@/hooks/use-auth";

describe("useAuth", () => {
  const mockUser = {
    id: "user-123",
    email: "test@example.com",
    app_metadata: {},
    user_metadata: {},
    aud: "authenticated",
    created_at: "2024-01-01",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetUser.mockResolvedValue({ data: { user: null } });
    mockOnAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: jest.fn() } },
    });
  });

  it("starts in loading state", () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.loading).toBe(true);
    expect(result.current.user).toBeNull();
  });

  it("resolves user from Supabase", async () => {
    mockGetUser.mockResolvedValue({ data: { user: mockUser } });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
  });

  it("sets user to null when not authenticated", async () => {
    mockGetUser.mockResolvedValue({ data: { user: null } });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
  });

  it("subscribes to auth state changes", () => {
    renderHook(() => useAuth());
    expect(mockOnAuthStateChange).toHaveBeenCalledTimes(1);
  });

  it("unsubscribes on unmount", () => {
    const unsubscribe = jest.fn();
    mockOnAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe } },
    });

    const { unmount } = renderHook(() => useAuth());
    unmount();

    expect(unsubscribe).toHaveBeenCalledTimes(1);
  });

  it("updates user on auth state change", async () => {
    let authCallback: (event: string, session: unknown) => void;
    mockOnAuthStateChange.mockImplementation(
      (cb: (event: string, session: unknown) => void) => {
        authCallback = cb;
        return { data: { subscription: { unsubscribe: jest.fn() } } };
      }
    );

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      authCallback!("SIGNED_IN", { user: mockUser });
    });

    expect(result.current.user).toEqual(mockUser);
  });

  it("signOut calls supabase.auth.signOut", async () => {
    mockSignOut.mockResolvedValue({});
    mockGetUser.mockResolvedValue({ data: { user: mockUser } });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // We can't easily test window.location.href in jsdom,
    // but we can verify signOut was called
    try {
      await act(async () => {
        await result.current.signOut();
      });
    } catch {
      // window.location.href assignment may throw in jsdom
    }

    expect(mockSignOut).toHaveBeenCalledTimes(1);
  });

  it("sets user to null on SIGNED_OUT event", async () => {
    let authCallback: (event: string, session: unknown) => void;
    mockOnAuthStateChange.mockImplementation(
      (cb: (event: string, session: unknown) => void) => {
        authCallback = cb;
        return { data: { subscription: { unsubscribe: jest.fn() } } };
      }
    );
    mockGetUser.mockResolvedValue({ data: { user: mockUser } });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    act(() => {
      authCallback!("SIGNED_OUT", null);
    });

    expect(result.current.user).toBeNull();
  });
});
