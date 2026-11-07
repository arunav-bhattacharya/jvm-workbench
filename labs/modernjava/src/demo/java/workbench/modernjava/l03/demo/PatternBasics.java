package workbench.modernjava.l03.demo;

/** The same dispatch three ways: an instanceof chain, a guard clause, and a pattern switch. */
public class PatternBasics {

    sealed interface Method permits Card, Transfer, Wallet {}

    record Card(String network, String last4) implements Method {}

    record Transfer(String iban) implements Method {}

    record Wallet(String provider) implements Method {}

    // an if-chain: javac never checks that it covers every Method
    static String viaChain(Method m) {
        if (m instanceof Card c) return "card " + c.network() + " ****" + c.last4();
        else if (m instanceof Transfer t) return "transfer from " + t.iban();
        else if (m instanceof Wallet w) return "wallet " + w.provider();
        else throw new IllegalStateException("unreachable?");
    }

    // a pattern switch: javac checks that every Method is covered
    static String viaSwitch(Method m) {
        return switch (m) {
            case Card c -> "card " + c.network() + " ****" + c.last4();
            case Transfer t -> "transfer from " + t.iban();
            case Wallet w -> "wallet " + w.provider();
        };
    }

    // flow scoping: after the negated test returns, c is in scope for the rest of the method
    static String last4(Object o) {
        if (!(o instanceof Card c)) return "not a card";
        return "last four: " + c.last4();
    }

    public static void main(String[] args) {
        Method[] all = { new Card("VISA", "1111"), new Transfer("DE89370400440532013000"), new Wallet("Paywave") };
        for (Method m : all) {
            System.out.println(viaChain(m) + "  |  " + viaSwitch(m));
        }
        System.out.println(last4(all[0]) + ", " + last4("4111"));
    }
}
