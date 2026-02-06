import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import SubscribeForm from "../SubscribeForm";

// Mock the api module
vi.mock("../../services/api", () => ({
  subscribe: vi.fn(),
}));

import { subscribe } from "../../services/api";

// Wrapper for components that use react-router-dom
const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("SubscribeForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders form fields correctly", () => {
    renderWithRouter(<SubscribeForm />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByText(/notify me via/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /subscribe/i })).toBeInTheDocument();
  });

  it("shows email field when email selected", () => {
    renderWithRouter(<SubscribeForm />);
    // Email is default selection
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/phone/i)).not.toBeInTheDocument();
  });

  it("renders notification preference selector", () => {
    renderWithRouter(<SubscribeForm />);

    // The select component uses Radix UI, which renders a combobox
    const selectTrigger = screen.getByRole("combobox");
    expect(selectTrigger).toBeInTheDocument();
    // Default value should be email
    expect(selectTrigger).toHaveTextContent(/email/i);
  });

  it("submits successfully and shows confirmation message", async () => {
    const user = userEvent.setup();
    vi.mocked(subscribe).mockResolvedValueOnce({
      id: "123",
      name: "Test",
      email: "test@example.com",
      phone: null,
      notification_preference: "email",
      confirmed: false,
      created_at: new Date().toISOString(),
    });

    renderWithRouter(<SubscribeForm />);

    await user.type(screen.getByLabelText(/name/i), "Test");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(screen.getByRole("button", { name: /subscribe/i }));

    await waitFor(() => {
      expect(screen.getByText(/check your inbox/i)).toBeInTheDocument();
    });
  });

  it("shows error on failed submission", async () => {
    const user = userEvent.setup();
    vi.mocked(subscribe).mockRejectedValueOnce({
      response: { data: { detail: "Email already subscribed" } },
    });

    renderWithRouter(<SubscribeForm />);

    await user.type(screen.getByLabelText(/name/i), "Test");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(screen.getByRole("button", { name: /subscribe/i }));

    await waitFor(() => {
      expect(screen.getByText(/email already subscribed/i)).toBeInTheDocument();
    });
  });
});
