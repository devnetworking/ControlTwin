import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders without crashing", () => {
    const { container } = render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    expect(container).toBeTruthy();
  });
});
