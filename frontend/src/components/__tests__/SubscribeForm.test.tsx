import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SubscribeForm from "../SubscribeForm";

// Mock the api module
vi.mock("../../services/api", () => ({
  subscribe: vi.fn(),
}));

import { subscribe } from "../../services/api";

describe("SubscribeForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders form fields correctly", () => {
    render(<SubscribeForm />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/notify me via/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /subscribe/i })).toBeInTheDocument();
  });

  it("shows email field when email selected", () => {
    render(<SubscribeForm />);
    // Email is default selection
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/phone/i)).not.toBeInTheDocument();
  });

  it("shows phone field when sms selected", async () => {
    const user = userEvent.setup();
    render(<SubscribeForm />);

    await user.selectOptions(screen.getByLabelText(/notify me via/i), "sms");

    expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
    expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
  });

  it("shows both fields when both selected", async () => {
    const user = userEvent.setup();
    render(<SubscribeForm />);

    await user.selectOptions(screen.getByLabelText(/notify me via/i), "both");

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
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

    render(<SubscribeForm />);

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

    render(<SubscribeForm />);

    await user.type(screen.getByLabelText(/name/i), "Test");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(screen.getByRole("button", { name: /subscribe/i }));

    await waitFor(() => {
      expect(screen.getByText(/email already subscribed/i)).toBeInTheDocument();
    });
  });
});
