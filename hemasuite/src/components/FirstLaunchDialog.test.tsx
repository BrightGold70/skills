import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FirstLaunchDialog } from "./FirstLaunchDialog";

describe("FirstLaunchDialog", () => {

  it("renders the welcome message", () => {
    render(<FirstLaunchDialog onDismiss={() => {}} />);
    expect(screen.getByText("Welcome to HemaSuite")).toBeInTheDocument();
  });

  it("renders Gatekeeper bypass instructions", () => {
    render(<FirstLaunchDialog onDismiss={() => {}} />);
    expect(screen.getByText(/right-click/i)).toBeInTheDocument();
  });

  it("calls onDismiss when button is clicked", () => {
    let dismissed = false;
    render(<FirstLaunchDialog onDismiss={() => { dismissed = true; }} />);
    fireEvent.click(screen.getByRole("button", { name: /got it/i }));
    expect(dismissed).toBe(true);
  });
});
