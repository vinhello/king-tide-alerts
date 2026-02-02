import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";

vi.mock("axios", () => {
  const mockAxios = {
    create: vi.fn(() => mockAxios),
    post: vi.fn(),
    get: vi.fn(),
  };
  return { default: mockAxios };
});

// Import after mocking
import {
  subscribe,
  confirmSubscription,
  unsubscribe,
  getUpcomingTides,
  createCheckoutSession,
} from "../api";

const mockedAxios = axios as unknown as {
  create: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
};

describe("API service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("subscribe calls POST /api/subscribe", async () => {
    const mockData = {
      id: "123",
      name: "Test",
      email: "test@example.com",
      phone: null,
      notification_preference: "email",
      confirmed: false,
      created_at: new Date().toISOString(),
    };
    mockedAxios.post.mockResolvedValueOnce({ data: mockData });

    const result = await subscribe({
      name: "Test",
      email: "test@example.com",
      notification_preference: "email",
    });

    expect(mockedAxios.post).toHaveBeenCalledWith("/api/subscribe", {
      name: "Test",
      email: "test@example.com",
      notification_preference: "email",
    });
    expect(result).toEqual(mockData);
  });

  it("confirmSubscription calls GET /api/confirm/:token", async () => {
    mockedAxios.get.mockResolvedValueOnce({
      data: { message: "Confirmed!" },
    });

    const result = await confirmSubscription("abc123");

    expect(mockedAxios.get).toHaveBeenCalledWith("/api/confirm/abc123");
    expect(result.message).toBe("Confirmed!");
  });

  it("unsubscribe calls GET /api/unsubscribe/:token", async () => {
    mockedAxios.get.mockResolvedValueOnce({
      data: { message: "Unsubscribed" },
    });

    const result = await unsubscribe("xyz789");

    expect(mockedAxios.get).toHaveBeenCalledWith("/api/unsubscribe/xyz789");
    expect(result.message).toBe("Unsubscribed");
  });

  it("getUpcomingTides calls GET /api/tides/upcoming", async () => {
    const mockResponse = {
      predictions: [],
      threshold: 1.0,
      station_id: "9414290",
    };
    mockedAxios.get.mockResolvedValueOnce({ data: mockResponse });

    const result = await getUpcomingTides(7);

    expect(mockedAxios.get).toHaveBeenCalledWith("/api/tides/upcoming?days=7");
    expect(result).toEqual(mockResponse);
  });

  it("createCheckoutSession calls POST /api/stripe/create-checkout-session", async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: { checkout_url: "https://checkout.stripe.com/test" },
    });

    const result = await createCheckoutSession();

    expect(mockedAxios.post).toHaveBeenCalledWith(
      "/api/stripe/create-checkout-session",
      { amount: 500 }
    );
    expect(result.checkout_url).toBe("https://checkout.stripe.com/test");
  });
});
