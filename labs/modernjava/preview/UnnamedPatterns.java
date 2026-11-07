// Needs JDK 22 or newer: unnamed variables and patterns (_) are final from JDK 22.
// On JDK 21 javac says "unnamed variables are a preview feature and are disabled by default".
// Run from labs/modernjava:   java preview/UnnamedPatterns.java

public class UnnamedPatterns {

    sealed interface Command permits Authorize, Capture, Refund, Decline {}

    record Authorize(String authCode, long amountMinor) implements Command {}

    record Capture() implements Command {}

    record Refund(long amountMinor) implements Command {}

    record Decline(String reason) implements Command {}

    // what may happen to a payment that is only Created so far
    static String onCreated(Command c) {
        return switch (c) {
            case Authorize(var code, _) -> "authorize with " + code;   // _ : a component you don't need
            case Decline(var reason) -> "fail: " + reason;
            case Capture _, Refund _ -> "not allowed yet";            // several patterns, one arm
        };
    }

    public static void main(String[] args) {
        System.out.println(onCreated(new Authorize("A1B2C3", 4_200)));
        System.out.println(onCreated(new Decline("insufficient funds")));
        System.out.println(onCreated(new Capture()));
        System.out.println(onCreated(new Refund(100)));
    }
}
