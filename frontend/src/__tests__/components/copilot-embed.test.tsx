import { render, screen, fireEvent } from "@testing-library/react";
import { CoPilotEmbed } from "@/components/copilot/copilot-embed";
import type { CoPilotState } from "@/hooks/use-copilot";

const defaultState: CoPilotState = {
  mounted: true,
  messages: [],
  isTyping: false,
  riskProfile: "moderate",
  locale: "en",
  confidence: 0.75,
  riskReward: { ratio: 2.5, rating: "good" },
  patterns: [],
  supportLevels: [],
  resistanceLevels: [],
};

describe("CoPilotEmbed", () => {
  it("renders JARVIS CO-PILOT label", () => {
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByText("JARVIS CO-PILOT")).toBeInTheDocument();
  });

  it("shows confidence tip card", () => {
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByText("Confidence: 75%")).toBeInTheDocument();
  });

  it("shows risk profile tip card", () => {
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByText("Risk: moderate")).toBeInTheDocument();
  });

  it("shows R:R tip card", () => {
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByText("R:R 2.5x")).toBeInTheDocument();
  });

  it("shows 'Awaiting data...' when confidence is 0", () => {
    const state = { ...defaultState, confidence: 0 };
    render(<CoPilotEmbed state={state} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByText("Awaiting data...")).toBeInTheDocument();
  });

  it("shows input field with placeholder", () => {
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByPlaceholderText("Frag JARVIS...")).toBeInTheDocument();
  });

  it("shows quick action buttons", () => {
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByText("📊")).toBeInTheDocument();
    expect(screen.getByText("🛡️")).toBeInTheDocument();
  });

  it("calls onExpand when expand button clicked", () => {
    const onExpand = jest.fn();
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={onExpand} />);
    fireEvent.click(screen.getByText("Expand").closest("button")!);
    expect(onExpand).toHaveBeenCalledTimes(1);
  });

  it("sends message on Enter key", () => {
    const sendMessage = jest.fn();
    render(<CoPilotEmbed state={defaultState} sendMessage={sendMessage} onExpand={jest.fn()} />);
    const input = screen.getByPlaceholderText("Frag JARVIS...");
    fireEvent.change(input, { target: { value: "test message" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(sendMessage).toHaveBeenCalledWith("test message");
  });

  it("does not send empty message", () => {
    const sendMessage = jest.fn();
    render(<CoPilotEmbed state={defaultState} sendMessage={sendMessage} onExpand={jest.fn()} />);
    const input = screen.getByPlaceholderText("Frag JARVIS...");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it("sends message on Send button click", () => {
    const sendMessage = jest.fn();
    render(<CoPilotEmbed state={defaultState} sendMessage={sendMessage} onExpand={jest.fn()} />);
    const input = screen.getByPlaceholderText("Frag JARVIS...");
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.click(screen.getByText("Send"));
    expect(sendMessage).toHaveBeenCalledWith("hello");
  });

  it("shows last analysis text when messages exist", () => {
    const state = {
      ...defaultState,
      messages: [
        { id: "1", role: "user" as const, content: "Hi", timestamp: new Date().toISOString() },
        { id: "2", role: "assistant" as const, content: "Strategy recommendation for today", timestamp: new Date().toISOString() },
      ],
    };
    const { container } = render(<CoPilotEmbed state={state} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    // The assistant message is rendered via dangerouslySetInnerHTML, search in container
    expect(container.textContent).toContain("recommendation");
  });

  it("shows placeholder when no messages", () => {
    render(<CoPilotEmbed state={defaultState} sendMessage={jest.fn()} onExpand={jest.fn()} />);
    expect(screen.getByText(/Ask JARVIS anything/i)).toBeInTheDocument();
  });
});
