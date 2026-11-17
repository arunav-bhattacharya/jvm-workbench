// Needs JDK 22 or newer: unnamed variables and patterns (_) are final from JDK 22.
// On JDK 21 javac says "unnamed variables are a preview feature and are disabled by default".
// Run from labs/modernjava:   java preview/UnnamedPatterns.java

public class UnnamedPatterns {

    sealed interface Request permits Borrow, Return, Renew, Withdraw {}

    record Borrow(String memberId, int days) implements Request {}

    record Return() implements Request {}

    record Renew(int extraDays) implements Request {}

    record Withdraw(String reason) implements Request {}

    // what may happen to a copy that is on the shelf right now
    static String onShelf(Request r) {
        return switch (r) {
            case Borrow(var member, _) -> "lend to " + member;         // _ : a component you don't need
            case Withdraw(var reason) -> "take off the shelf: " + reason;
            case Return _, Renew _ -> "not on loan";                   // several patterns, one arm
        };
    }

    public static void main(String[] args) {
        System.out.println(onShelf(new Borrow("M-1042", 21)));
        System.out.println(onShelf(new Withdraw("water damage")));
        System.out.println(onShelf(new Return()));
        System.out.println(onShelf(new Renew(14)));
    }
}
