import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SplashScreen } from "./SplashScreen";

describe("SplashScreen", () => {
  it("renders the app name", () => {
    render(<SplashScreen />);
    expect(screen.getByText("HemaSuite")).toBeInTheDocument();
  });

  it("renders the subtitle", () => {
    render(<SplashScreen />);
    expect(screen.getByText("Clinical Research Suite")).toBeInTheDocument();
  });

  it("shows a loading indicator", () => {
    render(<SplashScreen />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("displays startup message", () => {
    render(<SplashScreen />);
    expect(screen.getByText(/starting/i)).toBeInTheDocument();
  });

  it("displays developer credit", () => {
    render(<SplashScreen />);
    expect(
      screen.getByText("Developed by Hawk Kim, M.D., Ph.D.")
    ).toBeInTheDocument();
  });
});
